# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from neutron.db import servicetype_db as st_db
from neutron.services import provider_configuration as pconf
from neutron.services import service_base
from neutron_lib.api.definitions import portbindings
from neutron_lib.api.definitions import tap_mirror as t_m_api_def
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib.db import api as db_api
from neutron_lib import exceptions as n_exc
from neutron_lib.exceptions import taas as taas_exc
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

from neutron_taas.common import constants as taas_consts
from neutron_taas.db import tap_mirror_db
from neutron_taas.services.taas.service_drivers import (service_driver_context
                                                        as sd_context)

LOG = logging.getLogger(__name__)


@registry.has_registry_receivers
class TapMirrorPlugin(tap_mirror_db.Taas_mirror_db_mixin):

    supported_extension_aliases = [t_m_api_def.ALIAS]
    path_prefix = "/taas"

    def __init__(self):
        super().__init__()
        self.service_type_manager = st_db.ServiceTypeManager.get_instance()
        self.service_type_manager.add_provider_configuration(
            taas_consts.TAAS,
            pconf.ProviderConfiguration('neutron_taas'))

        # Load the service driver from neutron.conf.
        self.drivers, self.default_provider = service_base.load_drivers(
            taas_consts.TAAS, self)
        # Associate driver names to driver objects
        for driver_name, driver in self.drivers.items():
            driver.name = driver_name

        self.driver = self._get_driver_for_provider(self.default_provider)

        LOG.info(("Tap Mirror plugin using service drivers: "
                  "%(service_drivers)s, default: %(default_driver)s"),
                 {'service_drivers': self.drivers.keys(),
                  'default_driver': self.default_provider})

    def _get_driver_for_provider(self, provider):
        if provider in self.drivers:
            return self.drivers[provider]
        raise n_exc.Invalid("Error retrieving driver for provider %s" %
                            provider)

    @log_helpers.log_method_call
    def create_tap_mirror(self, context, tap_mirror):
        t_m = tap_mirror['tap_mirror']
        port_id = t_m['port_id']
        project_id = t_m['project_id']

        with db_api.CONTEXT_READER.using(context):
            # Get port details
            port = self.get_port_details(context, port_id)
            if port['tenant_id'] != project_id:
                raise taas_exc.PortDoesNotBelongToTenant()

            host = port[portbindings.HOST_ID]
            if host is not None:
                LOG.debug("Host on which the port is created = %s", host)
            else:
                LOG.debug("Host could not be found, Port Binding disbaled!")
                # Fail here? Is it a valid usecase to create a mirror for a
                # port that is not bound?

        with db_api.CONTEXT_WRITER.using(context):
            self._validate_tap_tunnel_id(context, t_m['directions'])
            tm = super().create_tap_mirror(context, tap_mirror)
            # Precommit phase, is it necessary? tunnel id check should be in
            # it....
            driver_context = sd_context.TapMirrorContext(self, context, tm)
            self.driver.create_tap_mirror_precommit(driver_context)

            # Postcommit phase, do the backend stuff, or fail.
            try:
                self.driver.create_tap_mirror_postcommit(driver_context)
            except Exception:
                pass
        return tm

    def _validate_tap_tunnel_id(self, context, mirror_directions):
        mirrors = self.get_tap_mirrors(context)
        for mirror in mirrors:
            for direction, tunnel_id in mirror['directions'].items():
                if tunnel_id in mirror_directions.values():
                    raise taas_exc.TapMirrorTunnelConflict(
                        tunnel_id=tunnel_id)

    @log_helpers.log_method_call
    def delete_tap_mirror(self, context, id):
        with db_api.CONTEXT_WRITER.using(context):
            tm = self.get_tap_mirror(context, id)

            if tm:
                # Precommit phase
                driver_context = sd_context.TapMirrorContext(
                    self, context, tm)
                self.driver.delete_tap_mirror_precommit(driver_context)

                # check if tunnel id was really deleted
                super().delete_tap_mirror(context, id)

            # Postcommit phase, do the backend stuff, or fail.
            try:
                self.driver.delete_tap_mirror_postcommit(driver_context)
            except Exception:
                with excutils.save_and_reraise_exception():
                    LOG.error("Failed to delete Tap Mirror on driver. "
                              "tap_mirror: %s", id)

    @registry.receives(resources.PORT, [events.PRECOMMIT_DELETE])
    @log_helpers.log_method_call
    def handle_delete_port(self, resource, event, trigger, payload):
        context = payload.context
        deleted_port = payload.latest_state
        if not deleted_port:
            LOG.error("Tap Mirror: Handle Delete Port: "
                      "Invalid port object received")
            return

        deleted_port_id = deleted_port['id']
        LOG.info("Tap Mirror: Handle Delete Port: %s", deleted_port_id)

        tap_mirrors = self.get_tap_mirrors(
            context,
            filters={'port_id': [deleted_port_id]}, fields=['id'])

        for t_m in tap_mirrors:
            try:
                self.delete_tap_mirror(context, t_m['id'])
            except taas_exc.TapMirrorNotFound:
                LOG.debug("Tap Mirror not found: %s", t_m['id'])
