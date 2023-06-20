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


from neutron.agent.common import ovs_lib
from neutron.agent.linux import utils
from neutron.conf.agent import common
from neutron_lib.plugins.ml2 import ovs_constants as n_ovs_consts

from neutron_taas.services.taas.agents.extensions import taas as taas_base
import neutron_taas.services.taas.drivers.linux.ovs_constants \
    as taas_ovs_consts
import neutron_taas.services.taas.drivers.linux.ovs_utils as taas_ovs_utils
from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging


LOG = logging.getLogger(__name__)

TaaS_DRIVER_NAME = 'Taas OVS driver'


class OVSBridge_tap_extension(ovs_lib.OVSBridge):
    def __init__(self, br_name, root_helper):
        super().__init__(br_name)


class OvsTaasDriver(taas_base.TaasAgentDriver):
    def __init__(self):
        super().__init__()
        LOG.debug("Initializing Taas OVS Driver")
        self.agent_api = None
        self.root_helper = common.get_root_helper(cfg.CONF)

    def initialize(self):
        self.int_br = self.agent_api.request_int_br()
        self.tun_br = self.agent_api.request_tun_br()
        self.tap_br = OVSBridge_tap_extension('br-tap', self.root_helper)

        # Prepare OVS bridges for TaaS
        self.setup_ovs_bridges()

        # Setup key-value manager for ingress BCMC flows
        self.bcmc_kvm = taas_ovs_utils.key_value_mgr(4096)

    def periodic_tasks(self, args=None):
        #
        # Regenerate the flow in br-tun's TAAS_SEND_FLOOD table
        # to ensure all existing tunnel ports are included.
        #
        self.update_tunnel_flood_flow()

    def setup_ovs_bridges(self):
        #
        # br-int : Integration Bridge
        # br-tap : Tap Bridge
        # br-tun : Tunnel Bridge
        #

        # Create br-tap
        self.tap_br.create()

        # Connect br-tap to br-int and br-tun
        self.int_br.add_patch_port('patch-int-tap', 'patch-tap-int')
        self.tap_br.add_patch_port('patch-tap-int', 'patch-int-tap')
        self.tun_br.add_patch_port('patch-tun-tap', 'patch-tap-tun')
        self.tap_br.add_patch_port('patch-tap-tun', 'patch-tun-tap')

        # Get patch port IDs
        patch_tap_int_id = self.tap_br.get_port_ofport('patch-tap-int')
        patch_tap_tun_id = self.tap_br.get_port_ofport('patch-tap-tun')
        patch_tun_tap_id = self.tun_br.get_port_ofport('patch-tun-tap')

        # Purge all existing Taas flows from br-tap and br-tun
        self.tap_br.delete_flows(table=0)
        self.tap_br.delete_flows(table=taas_ovs_consts.TAAS_RECV_LOC)
        self.tap_br.delete_flows(table=taas_ovs_consts.TAAS_RECV_REM)

        self.tun_br.delete_flows(table=0,
                                 in_port=patch_tun_tap_id)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SEND_UCAST)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SEND_FLOOD)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_CLASSIFY)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_DST_CHECK)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SRC_CHECK)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_DST_RESPOND)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SRC_RESPOND)

        #
        # Configure standard TaaS flows in br-tap
        #
        self.tap_br.add_flow(table=0,
                             priority=1,
                             in_port=patch_tap_int_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_RECV_LOC)

        self.tap_br.add_flow(table=0,
                             priority=1,
                             in_port=patch_tap_tun_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_RECV_REM)

        self.tap_br.add_flow(table=0,
                             priority=0,
                             actions="drop")

        self.tap_br.add_flow(table=taas_ovs_consts.TAAS_RECV_LOC,
                             priority=0,
                             actions="output:%s" % str(patch_tap_tun_id))

        self.tap_br.add_flow(table=taas_ovs_consts.TAAS_RECV_REM,
                             priority=0,
                             actions="drop")

        #
        # Configure standard Taas flows in br-tun
        #
        self.tun_br.add_flow(table=0,
                             priority=1,
                             in_port=patch_tun_tap_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_SEND_UCAST)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SEND_UCAST,
                             priority=0,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_SEND_FLOOD)

        flow_action = self._create_tunnel_flood_flow_action()
        if flow_action != "":
            self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SEND_FLOOD,
                                 priority=0,
                                 actions=flow_action)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_CLASSIFY,
                             priority=2,
                             reg0=0,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_DST_CHECK)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_CLASSIFY,
                             priority=1,
                             reg0=1,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_DST_CHECK)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_CLASSIFY,
                             priority=1,
                             reg0=2,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_SRC_CHECK)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_DST_CHECK,
                             priority=0,
                             actions="drop")

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SRC_CHECK,
                             priority=0,
                             actions="drop")

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_DST_RESPOND,
                             priority=2,
                             reg0=0,
                             actions="output:%s" % str(patch_tun_tap_id))

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_DST_RESPOND,
                             priority=1,
                             reg0=1,
                             actions=(
                                 "output:%s,"
                                 "move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID"
                                 "[0..11],mod_vlan_vid:2,output:in_port" %
                                 str(patch_tun_tap_id)))

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SRC_RESPOND,
                             priority=1,
                             actions=(
                                 "learn(table=%s,hard_timeout=60,"
                                 "priority=1,NXM_OF_VLAN_TCI[0..11],"
                                 "load:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID"
                                 "[0..11],load:0->NXM_OF_VLAN_TCI[0..11],"
                                 "output:NXM_OF_IN_PORT[])" %
                                 taas_ovs_consts.TAAS_SEND_UCAST))

    def consume_api(self, agent_api):
        self.agent_api = agent_api

    @log_helpers.log_method_call
    def create_tap_service(self, tap_service_msg):
        """Create a tap service

        :param tap_service_msg: a dict of the tap_service,
                                taas_id which is the VLAN Id reserved for
                                mirroring for this tap-service and the neutron
                                port of the tap-service:
                                {tap_service: {}, taas_id: VID, port: {}}
        """
        taas_id = tap_service_msg['taas_id']
        port = tap_service_msg['port']

        # Get OVS port id for tap service port
        ovs_port = self.int_br.get_vif_port_by_id(port['id'])
        ovs_port_id = ovs_port.ofport

        # Get VLAN id for tap service port
        port_dict = self.int_br.get_port_tag_dict()
        port_vlan_id = port_dict[ovs_port.port_name]

        # Get patch port IDs
        patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')
        patch_tap_int_id = self.tap_br.get_port_ofport('patch-tap-int')

        # Add flow(s) in br-int
        self.int_br.add_flow(table=0,
                             priority=25,
                             in_port=patch_int_tap_id,
                             dl_vlan=taas_id,
                             actions="mod_vlan_vid:%s,output:%s" %
                             (str(port_vlan_id), str(ovs_port_id)))

        # Add flow(s) in br-tap
        self.tap_br.add_flow(table=taas_ovs_consts.TAAS_RECV_LOC,
                             priority=1,
                             dl_vlan=taas_id,
                             actions="output:in_port")

        self.tap_br.add_flow(table=taas_ovs_consts.TAAS_RECV_REM,
                             priority=1,
                             dl_vlan=taas_id,
                             actions="output:%s" % str(patch_tap_int_id))

        # Add flow(s) in br-tun
        for tunnel_type in n_ovs_consts.TUNNEL_NETWORK_TYPES:
            self.tun_br.add_flow(table=n_ovs_consts.TUN_TABLE[tunnel_type],
                                 priority=1,
                                 tun_id=taas_id,
                                 actions=(
                                     "move:NXM_OF_VLAN_TCI[0..11]->"
                                     "NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID"
                                     "[0..11]->NXM_OF_VLAN_TCI[0..11],"
                                     "resubmit(,%s)" %
                                     taas_ovs_consts.TAAS_CLASSIFY))

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_DST_CHECK,
                             priority=1,
                             tun_id=taas_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_DST_RESPOND)

        #
        # Disable mac-address learning in the Linux bridge to which
        # the OVS port is attached (via the veth pair) if the system
        # uses OVSHybridIptablesFirewallDriver (Linux bridge & OVS).
        # This will effectively turn the bridge into a hub, ensuring
        # that all incoming mirrored traffic reaches the tap interface
        # (used for attaching a VM to the bridge) irrespective of the
        # destination mac addresses in mirrored packets.
        #

        # Get hybrid plug info
        vif_details = port.get('binding:vif_details')
        is_hybrid_plug = vif_details.get('ovs_hybrid_plug')

        if is_hybrid_plug:
            ovs_port_name = ovs_port.port_name
            linux_br_name = ovs_port_name.replace('qvo', 'qbr')
            utils.execute(['ip', 'link', 'set', linux_br_name,
                           'type', 'bridge', 'ageing_time', 0],
                          run_as_root=True, privsep_exec=True)

    @log_helpers.log_method_call
    def delete_tap_service(self, tap_service_msg):
        """Delete a tap service

        :param tap_service_msg: a dict of the tap_service,
                                taas_id which is the VLAN Id reserved for
                                mirroring for this tap-service and the neutron
                                port of the tap-service:
                                {tap_service: {}, taas_id: VID, port: {}}
        """
        taas_id = tap_service_msg['taas_id']

        # Get patch port ID
        patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')

        # Delete flow(s) from br-int
        self.int_br.delete_flows(table=0,
                                 in_port=patch_int_tap_id,
                                 dl_vlan=taas_id)

        # Delete flow(s) from br-tap
        self.tap_br.delete_flows(table=taas_ovs_consts.TAAS_RECV_LOC,
                                 dl_vlan=taas_id)

        self.tap_br.delete_flows(table=taas_ovs_consts.TAAS_RECV_REM,
                                 dl_vlan=taas_id)

        # Delete flow(s) from br-tun
        for tunnel_type in n_ovs_consts.TUNNEL_NETWORK_TYPES:
            self.tun_br.delete_flows(table=n_ovs_consts.TUN_TABLE[tunnel_type],
                                     tun_id=taas_id)

        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_DST_CHECK,
                                 tun_id=taas_id)

        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SRC_CHECK,
                                 tun_id=taas_id)

    @log_helpers.log_method_call
    def create_tap_flow(self, tap_flow_msg):
        """Create a tap flow

        :param tap_flow_msg: a dict of the tap_flow, the mac of the port of
                             the tap-flow, taas_id which is the VLAN Id
                             reserved for mirroring for the tap-service
                             associated with this tap-flow, the neutron port
                             of the tap-flow, and the port of the
                             tap-service:
                             {tap_flow: {}, port_mac: '', taas_id: VID,
                             port: {}, tap_service_port: {}}
        """
        taas_id = tap_flow_msg['taas_id']
        port = tap_flow_msg['port']
        direction = tap_flow_msg['tap_flow']['direction']

        # Get OVS port id for tap flow port
        ovs_port = self.int_br.get_vif_port_by_id(port['id'])
        ovs_port_id = ovs_port.ofport

        # Get patch port ID
        patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')

        # Add flow(s) in br-int
        if direction in ('OUT', 'BOTH'):
            self.int_br.add_flow(table=0,
                                 priority=20,
                                 in_port=ovs_port_id,
                                 actions="normal,mod_vlan_vid:%s,output:%s" %
                                 (str(taas_id), str(patch_int_tap_id)))

        if direction in ('IN', 'BOTH'):
            port_mac = tap_flow_msg['port_mac']

            #
            # Note: The ingress side flow (for unicast traffic) should
            #       include a check for the 'VLAN id of the Neutron
            #       network the port belongs to' + 'MAC address of the
            #       port', to comply with the requirement that port MAC
            #       addresses are unique only within a Neutron network.
            #       Unfortunately, at the moment there is no clean way
            #       to implement such a check, given OVS's handling of
            #       VLAN tags and Neutron's use of the NORMAL action in
            #       br-int.
            #
            #       We are therefore temporarily disabling the VLAN id
            #       check until a mechanism is available to implement
            #       it correctly. The {broad,multi}cast flow, which is
            #       also dependent on the VLAN id, has been disabled
            #       for the same reason.
            #

            # Get VLAN id for tap flow port
            # port_dict = self.int_br.get_port_tag_dict()
            # port_vlan_id = port_dict[ovs_port.port_name]

            self.int_br.add_flow(table=0,
                                 priority=20,
                                 # dl_vlan=port_vlan_id,
                                 dl_dst=port_mac,
                                 actions="normal,mod_vlan_vid:%s,output:%s" %
                                 (str(taas_id), str(patch_int_tap_id)))

            # self._add_update_ingress_bcmc_flow(port_vlan_id,
            #                                    taas_id,
            #                                    patch_int_tap_id)

        # Add flow(s) in br-tun
        for tunnel_type in n_ovs_consts.TUNNEL_NETWORK_TYPES:
            self.tun_br.add_flow(table=n_ovs_consts.TUN_TABLE[tunnel_type],
                                 priority=1,
                                 tun_id=taas_id,
                                 actions=(
                                     "move:NXM_OF_VLAN_TCI[0..11]->"
                                     "NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID"
                                     "[0..11]->NXM_OF_VLAN_TCI[0..11],"
                                     "resubmit(,%s)" %
                                     taas_ovs_consts.TAAS_CLASSIFY))

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SRC_CHECK,
                             priority=1,
                             tun_id=taas_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_SRC_RESPOND)

    @log_helpers.log_method_call
    def delete_tap_flow(self, tap_flow_msg):
        """Delete a tap flow

        :param tap_flow_msg: a dict of the tap_flow, the mac of the port of
                             the tap-flow, taas_id which is the VLAN Id
                             reserved for mirroring for the tap-service
                             associated with this tap-flow, the neutron port
                             of the tap-flow, the port of the
                             tap-service, the list of source VLAN IDs, and
                             VLAN filter list.
                             {tap_flow: {}, port_mac: '', taas_id: VID,
                             port: {}, tap_service_port: {},
                             source_vlans_list: [], vlan_filter_list: []}
        """
        port = tap_flow_msg['port']
        direction = tap_flow_msg['tap_flow']['direction']

        # Get OVS port id for tap flow port
        ovs_port = self.int_br.get_vif_port_by_id(port['id'])
        ovs_port_id = ovs_port.ofport

        # Delete flow(s) from br-int
        if direction in ('OUT', 'BOTH'):
            self.int_br.delete_flows(table=0,
                                     in_port=ovs_port_id)

        if direction in ('IN', 'BOTH'):
            port_mac = tap_flow_msg['port_mac']

            #
            # The VLAN id related checks have been temporarily disabled.
            # Please see comment in create_tap_flow() for details.
            #

            # taas_id = tap_flow['taas_id']

            # Get VLAN id for tap flow port
            # port_dict = self.int_br.get_port_tag_dict()
            # port_vlan_id = port_dict[ovs_port.port_name]

            # Get patch port ID
            # patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')

            self.int_br.delete_flows(table=0,
                                     # dl_vlan=port_vlan_id,
                                     dl_dst=port_mac)

            # self._del_update_ingress_bcmc_flow(port_vlan_id,
            #                                    taas_id,
            #                                    patch_int_tap_id)

    def update_tunnel_flood_flow(self):
        flow_action = self._create_tunnel_flood_flow_action()
        if flow_action != "":
            self.tun_br.mod_flow(table=taas_ovs_consts.TAAS_SEND_FLOOD,
                                 actions=flow_action)

    def _create_tunnel_flood_flow_action(self):
        port_name_list = self.tun_br.get_port_name_list()

        flow_action = ("move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID[0..11],"
                       "mod_vlan_vid:1")

        tunnel_ports_exist = False

        for port_name in port_name_list:
            if port_name not in ('patch-int', 'patch-tun-tap'):
                flow_action += (",output:%d" %
                                self.tun_br.get_port_ofport(port_name))
                tunnel_ports_exist = True

        if tunnel_ports_exist:
            return flow_action
        else:
            return ""

    def _create_ingress_bcmc_flow_action(self, taas_id_list, out_port_id):
        flow_action = "normal"
        for taas_id in taas_id_list:
            flow_action += (",mod_vlan_vid:%d,output:%d" %
                            (taas_id, out_port_id))

        return flow_action

    #
    # Adds or updates a special flow in br-int to mirror (duplicate and
    # redirect to 'out_port_id') all ingress broadcast/multicast traffic,
    # associated with a VLAN, to possibly multiple tap service instances.
    #
    def _add_update_ingress_bcmc_flow(self, vlan_id, taas_id, out_port_id):
        # Add a tap service instance affiliation with VLAN
        self.bcmc_kvm.affiliate(vlan_id, taas_id)

        # Find all tap service instances affiliated with VLAN
        taas_id_list = self.bcmc_kvm.list_affiliations(vlan_id)

        #
        # Add/update flow to mirror ingress BCMC traffic, associated
        # with VLAN, to all affiliated tap-service instances.
        #
        flow_action = self._create_ingress_bcmc_flow_action(taas_id_list,
                                                            out_port_id)
        self.int_br.add_flow(table=0,
                             priority=20,
                             dl_vlan=vlan_id,
                             dl_dst="01:00:00:00:00:00/01:00:00:00:00:00",
                             actions=flow_action)

    #
    # Removes or updates a special flow in br-int to mirror (duplicate
    # and redirect to 'out_port_id') all ingress broadcast/multicast
    # traffic, associated with a VLAN, to possibly multiple tap-service
    # instances.
    #
    def _del_update_ingress_bcmc_flow(self, vlan_id, taas_id, out_port_id):
        # Remove a tap-service instance affiliation with VLAN
        self.bcmc_kvm.unaffiliate(vlan_id, taas_id)

        # Find all tap-service instances affiliated with VLAN
        taas_id_list = self.bcmc_kvm.list_affiliations(vlan_id)

        #
        # If there are tap service instances affiliated with VLAN, update
        # the flow to mirror ingress BCMC traffic, associated with VLAN,
        # to all of them. Otherwise, remove the flow.
        #
        if taas_id_list:
            flow_action = self._create_ingress_bcmc_flow_action(taas_id_list,
                                                                out_port_id)
            self.int_br.add_flow(table=0,
                                 priority=20,
                                 dl_vlan=vlan_id,
                                 dl_dst="01:00:00:00:00:00/01:00:00:00:00:00",
                                 actions=flow_action)
        else:
            self.int_br.delete_flows(table=0,
                                     dl_vlan=vlan_id,
                                     dl_dst=("01:00:00:00:00:00/"
                                             "01:00:00:00:00:00"))
