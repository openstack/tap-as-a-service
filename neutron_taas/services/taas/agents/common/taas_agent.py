# Copyright (C) 2018 AT&T
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


from neutron import manager
from neutron_taas.services.taas.drivers.linux \
    import ovs_constants as taas_ovs_consts

from neutron_taas.common import topics
from neutron_taas.services.taas.agents import taas_agent_api as api

from neutron_lib.api.definitions import portbindings
from neutron_lib import constants
from neutron_lib import context as neutron_context
from neutron_lib import rpc as n_rpc
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import service

LOG = logging.getLogger(__name__)


class TaasPluginApi(api.TaasPluginApiMixin):

    def __init__(self, topic, host):
        super(TaasPluginApi, self).__init__(topic, host)
        target = messaging.Target(topic=topic, version='1.0')
        self.client = n_rpc.get_client(target)
        return

    def sync_tap_resources(self, sync_tap_res, host):
        """Send Rpc to plugin to recreate pre-existing tap resources."""
        LOG.debug("In RPC Call for Sync Tap Resources: Host=%s, MSG=%s" %
                  (host, sync_tap_res))

        context = neutron_context.get_admin_context()

        cctxt = self.client.prepare(fanout=False)
        cctxt.cast(context, 'sync_tap_resources', sync_tap_res=sync_tap_res,
                   host=host)

        return

    def set_tap_service_status(self, msg, status, host):
        LOG.debug("In RPC Call for set tap service status: Host=%s, MSG=%s, "
                  "Status=%s" %
                  (host, msg, status))

        context = neutron_context.get_admin_context()

        cctxt = self.client.prepare(fanout=False)
        cctxt.cast(context, 'set_tap_service_status', msg=msg, status=status,
                   host=host)

        return

    def set_tap_flow_status(self, msg, status, host):
        LOG.debug("In RPC Call for set tap flow status: Host=%s, MSG=%s, "
                  "Status=%s" %
                  (host, msg, status))

        context = neutron_context.get_admin_context()

        cctxt = self.client.prepare(fanout=False)
        cctxt.cast(context, 'set_tap_flow_status', msg=msg, status=status,
                   host=host)

        return


class TaasAgentRpcCallback(api.TaasAgentRpcCallbackMixin):

    def __init__(self, conf, driver_type):

        LOG.debug("TaaS Agent initialize called")

        self.conf = conf
        self.driver_type = driver_type

        super(TaasAgentRpcCallback, self).__init__()

    def initialize(self):
        self.taas_driver = manager.NeutronManager.load_class_for_provider(
            'neutron_taas.taas.agent_drivers', self.driver_type)()
        self.taas_driver.consume_api(self.agent_api)
        self.taas_driver.initialize()
        self.func_dict = {
            'create_tap_service': {
                'msg_name': 'tap_service',
                'set_status_func_name': 'set_tap_service_status',
                'fail_status': constants.ERROR,
                'succ_status': constants.ACTIVE},
            'create_tap_flow': {
                'msg_name': 'tap_flow',
                'set_status_func_name': 'set_tap_flow_status',
                'fail_status': constants.ERROR,
                'succ_status': constants.ACTIVE},
            'delete_tap_service': {
                'msg_name': 'tap_service',
                'set_status_func_name': 'set_tap_service_status',
                'fail_status': constants.PENDING_DELETE,
                'succ_status': constants.INACTIVE},
            'delete_tap_flow': {
                'msg_name': 'tap_flow',
                'set_status_func_name': 'set_tap_flow_status',
                'fail_status': constants.PENDING_DELETE,
                'succ_status': constants.INACTIVE}
        }
        self.portbind_drivers_map = {portbindings.VNIC_DIRECT: 'sriov',
                                     portbindings.VNIC_NORMAL: 'ovs'}
        self._taas_rpc_setup()
        TaasAgentService(self).start(self.taas_plugin_rpc, self.conf.host)

    def consume_api(self, agent_api):
        self.agent_api = agent_api

    def _invoke_driver_for_plugin_api(self, context, args, func_name):
        LOG.debug("Invoking Driver for %(func_name)s from agent",
                  {'func_name': func_name})

        status_msg = {'id': args[self.func_dict[func_name]['msg_name']]['id']}

        try:
            self.taas_driver.__getattribute__(func_name)(args)
        except Exception:
            LOG.error("Failed to invoke the driver")

            self.taas_plugin_rpc.__getattribute__(
                self.func_dict[func_name]['set_status_func_name'])(
                    status_msg,
                    self.func_dict[func_name]['fail_status'],
                    self.conf.host)
            return

        self.taas_plugin_rpc.__getattribute__(
            self.func_dict[func_name]['set_status_func_name'])(
                status_msg,
                self.func_dict[func_name]['succ_status'],
                self.conf.host)

    def create_tap_service(self, context, tap_service, host):
        """Handle Rpc from plugin to create a tap_service."""
        if not self._driver_and_host_verification(host, tap_service['port']):
            LOG.debug("RPC Call for Create Tap Serv. Either Host value [%s]"
                      "(received in RPC) doesn't match the host value "
                      "stored in agent [%s], or incompatible driver type. "
                      "Ignoring the message." % (host, self.conf.host))
            return
        LOG.debug("In RPC Call for Create Tap Service: MSG=%s" % tap_service)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_service,
            'create_tap_service')

    def create_tap_flow(self, context, tap_flow_msg, host):
        if not self._driver_and_host_verification(host, tap_flow_msg['port']):
            LOG.debug("RPC Call for Create Tap Flow. Either Host value [%s]"
                      "(received in RPC) doesn't match the host value "
                      "stored in agent [%s], or incompatible driver type. "
                      "Ignoring the message." % (host, self.conf.host))
            return
        LOG.debug("In RPC Call for Create Tap Flow: MSG=%s" % tap_flow_msg)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_flow_msg,
            'create_tap_flow')

    def delete_tap_service(self, context, tap_service, host):
        #
        # Cleanup operations must be performed by all hosts
        # where the source and/or destination ports associated
        # with this tap service were residing.
        #
        if not self._is_driver_port_type_compatible(tap_service['port']):
            LOG.debug("RPC Call for Delete Tap Service. Incompatible driver "
                      "type. Ignoring the message. Host=[%s]" % (host))
            return
        LOG.debug("In RPC Call for Delete Tap Service: MSG=%s" % tap_service)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_service,
            'delete_tap_service')

    def delete_tap_flow(self, context, tap_flow_msg, host):
        if not self._driver_and_host_verification(host, tap_flow_msg['port']):
            LOG.debug("RPC Call for Delete Tap Flow. Either Host value [%s]"
                      "(received in RPC) doesn't match the host value "
                      "stored in agent [%s], or incompatible driver type. "
                      "Ignoring the message." % (host, self.conf.host))
            return
        LOG.debug("In RPC Call for Delete Tap Flow: MSG=%s" % tap_flow_msg)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_flow_msg,
            'delete_tap_flow')

    def _taas_rpc_setup(self):
        # setup RPC to msg taas plugin
        self.taas_plugin_rpc = TaasPluginApi(
            topics.TAAS_PLUGIN, self.conf.host)

        endpoints = [self]
        conn = n_rpc.Connection()
        conn.create_consumer(topics.TAAS_AGENT, endpoints, fanout=False)
        conn.consume_in_threads()

    def periodic_tasks(self):
        return self._invoke_driver_for_plugin_api(
            context=None,
            args=None,
            func_name='periodic_tasks')

    def get_driver_type(self):
        return self.driver_type

    def _is_driver_port_type_compatible(self, port):
        return (
            port.get(portbindings.VNIC_TYPE) in self.portbind_drivers_map and
            self.portbind_drivers_map[port.get(portbindings.VNIC_TYPE)] ==
            self.driver_type)

    def _driver_and_host_verification(self, host, port):
        return ((host == self.conf.host) and
                self._is_driver_port_type_compatible(port))


class TaasAgentService(service.Service):
    def __init__(self, driver):
        super(TaasAgentService, self).__init__()
        self.driver = driver

    def start(self, taas_plugin_rpc, host):
        super(TaasAgentService, self).start()

        if self.driver.get_driver_type() == \
                taas_ovs_consts.EXTENSION_DRIVER_TYPE:
            self.tg.add_timer(
                int(cfg.CONF.taas_agent_periodic_interval),
                self.driver.periodic_tasks,
                None
            )

        # Indicate the TaaS plugin to recreate the taas resources
        rpc_msg = {'host_id': host}
        taas_plugin_rpc.sync_tap_resources(rpc_msg, host)
