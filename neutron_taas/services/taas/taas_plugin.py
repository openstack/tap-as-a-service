# Copyright (C) 2016 Midokura SARL.
# Copyright (C) 2015 Ericsson AB
# Copyright (c) 2015 Gigamon
#
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
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib import constants
from neutron_lib.db import api as db_api
from neutron_lib import exceptions as n_exc
from neutron_lib.exceptions import taas as taas_exc

from neutron_taas.common import constants as taas_consts
from neutron_taas.db import taas_db
from neutron_taas.services.taas.service_drivers import (service_driver_context
                                                        as sd_context)

from oslo_log import log as logging
from oslo_utils import excutils

LOG = logging.getLogger(__name__)


def add_provider_configuration(type_manager, service_type):
    type_manager.add_provider_configuration(
        service_type,
        pconf.ProviderConfiguration('neutron_taas'))


@registry.has_registry_receivers
class TaasPlugin(taas_db.Taas_db_Mixin):

    supported_extension_aliases = ["taas",
                                   "taas-vlan-filter"]
    path_prefix = "/taas"

    def __init__(self):

        LOG.debug("TAAS PLUGIN INITIALIZATION")
        self.service_type_manager = st_db.ServiceTypeManager.get_instance()
        add_provider_configuration(self.service_type_manager,
                                   taas_consts.TAAS)
        self._load_drivers()
        self.driver = self._get_driver_for_provider(self.default_provider)
        LOG.info(("TAAS Plugin initialized using service drivers: "
                  "%(service_drivers)s, default: %(default_driver)s"),
                 {'service_drivers': self.drivers.keys(),
                  'default_driver': self.default_provider})

    def _load_drivers(self):
        """Loads plugin-drivers specified in configuration."""
        self.drivers, self.default_provider = service_base.load_drivers(
            taas_consts.TAAS, self)

    def _get_driver_for_provider(self, provider):
        if provider in self.drivers:
            return self.drivers[provider]
        raise n_exc.Invalid("Error retrieving driver for provider %s" %
                            provider)

    @db_api.CONTEXT_WRITER
    def create_tap_service(self, context, tap_service):
        LOG.debug("create_tap_service() called")

        t_s = tap_service['tap_service']
        tenant_id = t_s['tenant_id']
        port_id = t_s['port_id']

        # Get port details
        port = self.get_port_details(context, port_id)

        # Check if the port is owned by the tenant.
        if port['tenant_id'] != tenant_id:
            raise taas_exc.PortDoesNotBelongToTenant()

        # Extract the host where the port is located
        host = port['binding:host_id']

        if host is not None:
            LOG.debug("Host on which the port is created = %s", host)
        else:
            LOG.debug("Host could not be found, Port Binding disbaled!")

        # Create tap service in the db model
        ts = super().create_tap_service(context, tap_service)
        driver_context = sd_context.TapServiceContext(self, context, ts)
        self.driver.create_tap_service_precommit(driver_context)

        try:
            self.driver.create_tap_service_postcommit(driver_context)
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create tap service on driver,"
                          "deleting tap_service %s", ts['id'])
                super().delete_tap_service(context, ts['id'])

        return ts

    @db_api.CONTEXT_WRITER
    def delete_tap_service(self, context, id):
        LOG.debug("delete_tap_service() called")

        # Get all the tap Flows that are associated with the Tap service
        # and delete them as well
        t_f_collection = self.get_tap_flows(
            context,
            filters={'tap_service_id': [id]}, fields=['id'])

        for t_f in t_f_collection:
            self.delete_tap_flow(context, t_f['id'])

        ts = self.get_tap_service(context, id)
        driver_context = sd_context.TapServiceContext(self, context, ts)
        if ts['status'] == constants.ACTIVE:
            ts['status'] = constants.PENDING_DELETE
            super().update_tap_service(
                context, id, {'tap_service': ts})
            method = self.driver.delete_tap_service_precommit
        else:
            super().delete_tap_service(context, id)
            method = self.driver.delete_tap_service_postcommit

        try:
            method(driver_context)
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to delete tap service on driver. "
                          "tap_sevice: %s", id)

    @db_api.CONTEXT_WRITER
    def create_tap_flow(self, context, tap_flow):
        LOG.debug("create_tap_flow() called")

        t_f = tap_flow['tap_flow']
        tenant_id = t_f['tenant_id']

        # Check if the tenant id of the source port is the same as the
        # tenant_id of the tap service we are attaching it to.

        ts = self.get_tap_service(context, t_f['tap_service_id'])
        ts_tenant_id = ts['tenant_id']

        if tenant_id != ts_tenant_id:
            raise taas_exc.TapServiceNotBelongToTenant()

        # create tap flow in the db model
        tf = super().create_tap_flow(context, tap_flow)
        driver_context = sd_context.TapFlowContext(self, context, tf)
        self.driver.create_tap_flow_precommit(driver_context)

        try:
            self.driver.create_tap_flow_postcommit(driver_context)
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create tap flow on driver,"
                          "deleting tap_flow %s", tf['id'])
                super().delete_tap_flow(context, tf['id'])

        return tf

    @db_api.CONTEXT_WRITER
    def delete_tap_flow(self, context, id):
        LOG.debug("delete_tap_flow() called")

        tf = self.get_tap_flow(context, id)
        driver_context = sd_context.TapFlowContext(self, context, tf)
        if tf['status'] == constants.ACTIVE:
            tf['status'] = constants.PENDING_DELETE
            super().update_tap_flow(context, id, {'tap_flow': tf})
            method = self.driver.delete_tap_flow_precommit
        else:
            super().delete_tap_flow(context, id)
            method = self.driver.delete_tap_flow_postcommit

        try:
            method(driver_context)
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to delete tap flow on driver. "
                          "tap_flow: %s", id)

    @registry.receives(resources.PORT, [events.PRECOMMIT_DELETE])
    def handle_delete_port(self, resource, event, trigger, payload):
        context = payload.context
        deleted_port = payload.latest_state
        if not deleted_port:
            LOG.error("TaaS: Handle Delete Port: Invalid port object received")
            return

        deleted_port_id = deleted_port['id']
        LOG.info("TaaS: Handle Delete Port: %s", deleted_port_id)

        # Get list of configured tap-services
        t_s_collection = self.get_tap_services(
            context,
            filters={'port_id': [deleted_port_id]}, fields=['id'])

        for t_s in t_s_collection:
            try:
                self.delete_tap_service(context, t_s['id'])
            except taas_exc.TapServiceNotFound:
                LOG.debug("Not found tap_service: %s", t_s['id'])

        t_f_collection = self.get_tap_flows(
            context,
            filters={'source_port': [deleted_port_id]}, fields=['id'])

        for t_f in t_f_collection:
            try:
                self.delete_tap_flow(context, t_f['id'])
            except taas_exc.TapFlowNotFound:
                LOG.debug("Not found tap_flow: %s", t_f['id'])
