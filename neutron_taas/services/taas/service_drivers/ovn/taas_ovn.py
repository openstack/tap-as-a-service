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

from neutron_lib.api.definitions import tap_mirror as tap_m_api_def
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron_taas.services.taas import service_drivers
from neutron_taas.services.taas.service_drivers.ovn import helper


LOG = logging.getLogger(__name__)


class TaasOvnDriver(service_drivers.TaasBaseDriver):
    """Taas OVN Service Driver class"""

    more_supported_extension_aliases = [tap_m_api_def.ALIAS]

    def __init__(self, service_plugin):
        LOG.debug("Loading Taas OVN Driver.")
        super().__init__(service_plugin)
        self._ovn_helper = helper.TaasOvnProviderHelper()

    def __del__(self):
        self._ovn_helper.shutdown()

    @log_helpers.log_method_call
    def create_tap_service_precommit(self, context):
        LOG.warning("Not implemented")

    @log_helpers.log_method_call
    def create_tap_service_postcommit(self, context):
        LOG.warning("Not implemented")

    @log_helpers.log_method_call
    def delete_tap_service_precommit(self, context):
        LOG.warning("Not implemented")

    @log_helpers.log_method_call
    def delete_tap_service_postcommit(self, context):
        LOG.warning("Not implemented")

    @log_helpers.log_method_call
    def create_tap_flow_precommit(self, context):
        LOG.warning("Not implemented")

    @log_helpers.log_method_call
    def create_tap_flow_postcommit(self, context):
        LOG.warning("Not implemented")

    @log_helpers.log_method_call
    def delete_tap_flow_precommit(self, context):
        """Send tap flow deletion RPC message to agent."""
        LOG.warning("Not implemented")

    @log_helpers.log_method_call
    def delete_tap_flow_postcommit(self, context):
        LOG.warning("Not implemented")

    @log_helpers.log_method_call
    def create_tap_mirror_precommit(self, context):
        pass

    @log_helpers.log_method_call
    def create_tap_mirror_postcommit(self, context):
        LOG.info('create_tap_mirror_postcommit %s', context.tap_mirror)
        t_m = context.tap_mirror
        type = 'erspan' if 'erspan' in t_m['mirror_type'] else 'gre'
        directions = t_m['directions']
        for direction, tunnel_id in directions.items():
            mirror_port_name = 'tm_%s_%s' % (direction.lower(), t_m['id'][0:6])
            ovn_direction = ('from-lport' if direction == 'OUT'
                             else 'to-lport')
            request = {'type': 'mirror_add',
                       'info': {'name': mirror_port_name,
                                'direction_filter': ovn_direction,
                                'dest': t_m['remote_ip'],
                                'mirror_type': type,
                                'index': int(tunnel_id),
                                'port_id': t_m['port_id']}}
            self._ovn_helper.add_request(request)

    @log_helpers.log_method_call
    def delete_tap_mirror_precommit(self, context):
        LOG.info('delete_tap_mirror_precommit %s', context.tap_mirror)
        t_m = context.tap_mirror
        directions = t_m['directions']
        for direction, tunnel_id in directions.items():
            mirror_port_name = 'tm_%s_%s' % (direction.lower(), t_m['id'][0:6])
            request = {
                'type': 'mirror_del',
                'info': {'id': t_m['id'],
                         'name': mirror_port_name,
                         'sink': t_m['remote_ip'],
                         'port_id': t_m['port_id']}
            }
            self._ovn_helper.add_request(request)

    @log_helpers.log_method_call
    def delete_tap_mirror_postcommit(self, context):
        pass
