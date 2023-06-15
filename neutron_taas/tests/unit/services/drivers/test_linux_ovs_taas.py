#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from unittest import mock

from neutron_lib.plugins.ml2 import ovs_constants as n_ovs_consts

import neutron_taas.services.taas.drivers.linux.ovs_constants \
    as taas_ovs_consts
from neutron_taas.services.taas.drivers.linux import ovs_taas
from neutron_taas.tests import base


class FakeVifPort(object):
    def __init__(self, port_name, ofport, vif_id, vif_mac, switch):
        self.port_name = port_name
        self.ofport = ofport
        self.vif_id = vif_id
        self.vif_mac = vif_mac
        self.switch = switch


class FakeBridge(object):

    def __init__(self, br_name):
        self.br_name = br_name

    def add_patch_port(self, local_name, remote_name):
        pass

    def get_port_ofport(self, port_name):
        return base.FAKE_OF_PORT

    def add_flow(self, **kwargs):
        pass

    def delete_flows(self, **kwargs):
        pass

    def get_vif_port_by_id(self, port_id):
        port = base.FAKE_TAP_SERVICE_OVS['port']
        return FakeVifPort(
            port_name=base.FAKE_OF_PORT['port_name'],
            ofport=base.FAKE_OF_PORT['ofport'],
            vif_id=port_id,
            vif_mac=port['mac_address'],
            switch=port['binding:vif_details']['bridge_name']
        )

    def get_port_tag_dict(self):
        return base.FAKE_PORT_DICT


class TestOvsDriverTaas(base.TaasTestCase):

    def setUp(self):
        super(TestOvsDriverTaas, self).setUp()

    def _create_tun_flood_flow(self):
        return ''

    def _init_taas_driver(self, mock_ovs_ext_api, mock_tap_ext):
        obj = ovs_taas.OvsTaasDriver()
        obj.agent_api = mock_ovs_ext_api
        obj.tunnel_types = 'vxlan'

        obj._create_tunnel_flood_flow_action = self._create_tun_flood_flow

        mock_br_int = mock_ovs_ext_api.request_int_br.return_value
        mock_br_int.add_flow = mock.Mock()
        mock_br_int.delete_flows = mock.Mock()
        mock_br_int.add_patch_port = mock.Mock()

        mock_br_tun = mock_ovs_ext_api.request_tun_br.return_value
        mock_br_tun.add_flow = mock.Mock()
        mock_br_tun.delete_flows = mock.Mock()
        mock_br_tun.add_patch_port = mock.Mock()

        mock_tap_bridge = mock_tap_ext.return_value
        mock_tap_bridge.create.return_value = None
        mock_tap_bridge.add_flow = mock.Mock()
        mock_tap_bridge.delete_flows = mock.Mock()

        obj.initialize()

        return obj, mock_tap_bridge, mock_br_int, mock_br_tun

    def _vlidate_bridge_initialization(self, mock_ovs_ext_api,
                                       mock_tap_bridge, mock_br_int,
                                       mock_br_tun):
        mock_ovs_ext_api.request_int_br.assert_called_once()
        mock_ovs_ext_api.request_tun_br.assert_called_once()

        mock_tap_bridge.create.assert_called_once()

        mock_br_int.add_patch_port.assert_called_once()
        mock_br_tun.add_patch_port.assert_called_once()
        mock_tap_bridge.add_patch_port.assert_has_calls([
            mock.call('patch-tap-int', 'patch-int-tap'),
            mock.call('patch-tap-tun', 'patch-tun-tap')
        ])

        mock_tap_bridge.add_flow.assert_has_calls([
            mock.call(table=0, priority=1, in_port=mock.ANY,
                      actions='resubmit(,1)'),
            mock.call(table=0, priority=1, in_port=mock.ANY,
                      actions='resubmit(,2)'),
            mock.call(table=0, priority=0, actions='drop'),
            mock.call(table=1, priority=0, actions=mock.ANY),
            mock.call(table=2, priority=0, actions='drop'),
        ])

        mock_br_tun.add_flow.assert_has_calls([
            mock.call(table=0, priority=1, in_port=mock.ANY,
                      actions='resubmit(,30)'),
            mock.call(table=30, priority=0, actions='resubmit(,31)'),
            mock.call(table=35, priority=2, reg0=0, actions='resubmit(,36)'),
            mock.call(table=35, priority=1, reg0=1, actions='resubmit(,36)'),
            mock.call(table=35, priority=1, reg0=2, actions='resubmit(,37)'),
            mock.call(table=36, priority=0, actions='drop'),
            mock.call(table=37, priority=0, actions='drop'),
            mock.call(table=38, priority=2, reg0=0, actions=mock.ANY),
            mock.call(table=38, priority=1, reg0=1, actions=mock.ANY),
            mock.call(table=39, priority=1, actions=mock.ANY)
        ])

    @mock.patch('neutron.plugins.ml2.drivers.openvswitch.agent.'
                'ovs_agent_extension_api.OVSAgentExtensionAPI')
    @mock.patch('neutron_taas.services.taas.drivers.linux.ovs_taas.'
                'OVSBridge_tap_extension')
    def test_create_tap_service(self, mock_tap_ext, mock_api):
        tap_service = base.FAKE_TAP_SERVICE_OVS

        mock_ovs_ext_api = mock_api.return_value
        mock_ovs_ext_api.request_int_br.return_value = FakeBridge('br_int')
        mock_ovs_ext_api.request_tun_br.return_value = FakeBridge('br_tun')

        obj, mock_tap_bridge, mock_br_int, mock_br_tun = \
            self._init_taas_driver(mock_ovs_ext_api, mock_tap_ext)
        self._vlidate_bridge_initialization(mock_ovs_ext_api, mock_tap_bridge,
                                            mock_br_int, mock_br_tun)

        mock_tap_bridge.reset_mock()
        mock_br_int.add_flow.reset_mock()
        mock_br_tun.add_flow.reset_mock()
        with mock.patch('neutron.agent.linux.utils.execute'):
            obj.create_tap_service(tap_service)

        mock_tap_bridge.add_flow.assert_has_calls([
            mock.call(table=1, priority=1, dl_vlan=mock.ANY,
                      actions='output:in_port'),
            mock.call(table=2, priority=1, dl_vlan=mock.ANY, actions=mock.ANY)
        ])
        mock_br_int.add_flow.assert_called_once_with(
            table=0, priority=25, in_port=mock.ANY, dl_vlan=mock.ANY,
            actions=mock.ANY
        )
        mock_br_tun.add_flow.assert_has_calls([
            mock.call(table=n_ovs_consts.GRE_TUN_TO_LV, priority=1,
                      tun_id=mock.ANY, actions=mock.ANY),
            mock.call(table=n_ovs_consts.VXLAN_TUN_TO_LV, priority=1,
                      tun_id=mock.ANY, actions=mock.ANY),
            mock.call(table=n_ovs_consts.GENEVE_TUN_TO_LV, priority=1,
                      tun_id=mock.ANY, actions=mock.ANY),
            mock.call(table=taas_ovs_consts.TAAS_DST_CHECK, priority=1,
                      tun_id=mock.ANY, actions='resubmit(,38)')
        ])

    @mock.patch('neutron.plugins.ml2.drivers.openvswitch.agent.'
                'ovs_agent_extension_api.OVSAgentExtensionAPI')
    @mock.patch('neutron_taas.services.taas.drivers.linux.ovs_taas.'
                'OVSBridge_tap_extension')
    def test_delete_tap_service(self, mock_tap_ext, mock_api):
        tap_service = base.FAKE_TAP_SERVICE_OVS

        mock_ovs_ext_api = mock_api.return_value
        mock_ovs_ext_api.request_int_br.return_value = FakeBridge('br_int')
        mock_ovs_ext_api.request_tun_br.return_value = FakeBridge('br_tun')

        obj, mock_tap_bridge, mock_br_int, mock_br_tun = \
            self._init_taas_driver(mock_ovs_ext_api, mock_tap_ext)
        self._vlidate_bridge_initialization(mock_ovs_ext_api, mock_tap_bridge,
                                            mock_br_int, mock_br_tun)

        mock_tap_bridge.delete_flows.reset_mock()
        mock_br_int.delete_flows.reset_mock()
        mock_br_tun.delete_flows.reset_mock()

        obj.delete_tap_service(tap_service)

        mock_tap_bridge.delete_flows.assert_has_calls([
            mock.call(table=1, dl_vlan=mock.ANY),
            mock.call(table=2, dl_vlan=mock.ANY),
        ])
        mock_br_int.delete_flows.assert_called_once_with(
            table=0, in_port=mock.ANY, dl_vlan=mock.ANY,
        )
        mock_br_tun.delete_flows.assert_has_calls([
            mock.call(table=n_ovs_consts.GRE_TUN_TO_LV, tun_id=mock.ANY),
            mock.call(table=n_ovs_consts.VXLAN_TUN_TO_LV, tun_id=mock.ANY),
            mock.call(table=n_ovs_consts.GENEVE_TUN_TO_LV, tun_id=mock.ANY),
            mock.call(table=taas_ovs_consts.TAAS_DST_CHECK, tun_id=mock.ANY),
            mock.call(table=taas_ovs_consts.TAAS_SRC_CHECK, tun_id=mock.ANY)
        ])

    @mock.patch('neutron.plugins.ml2.drivers.openvswitch.agent.'
                'ovs_agent_extension_api.OVSAgentExtensionAPI')
    @mock.patch('neutron_taas.services.taas.drivers.linux.ovs_taas.'
                'OVSBridge_tap_extension')
    def test_create_tap_flow(self, mock_tap_ext, mock_api):
        tap_flow = base.FAKE_TAP_FLOW

        mock_ovs_ext_api = mock_api.return_value
        mock_ovs_ext_api.request_int_br.return_value = FakeBridge('br_int')
        mock_ovs_ext_api.request_tun_br.return_value = FakeBridge('br_tun')

        obj, mock_tap_bridge, mock_br_int, mock_br_tun = \
            self._init_taas_driver(mock_ovs_ext_api, mock_tap_ext)
        self._vlidate_bridge_initialization(mock_ovs_ext_api, mock_tap_bridge,
                                            mock_br_int, mock_br_tun)

        mock_tap_bridge.reset_mock()
        mock_br_int.add_flow.reset_mock()
        mock_br_tun.add_flow.reset_mock()
        obj.create_tap_flow(tap_flow)

        mock_tap_bridge.add_flow.assert_not_called()
        mock_br_tun.add_flow.assert_has_calls([
            mock.call(table=n_ovs_consts.GRE_TUN_TO_LV, priority=1,
                      tun_id=mock.ANY, actions=mock.ANY),
            mock.call(table=n_ovs_consts.VXLAN_TUN_TO_LV, priority=1,
                      tun_id=mock.ANY, actions=mock.ANY),
            mock.call(table=n_ovs_consts.GENEVE_TUN_TO_LV, priority=1,
                      tun_id=mock.ANY, actions=mock.ANY),
            mock.call(table=taas_ovs_consts.TAAS_SRC_CHECK, priority=1,
                      tun_id=mock.ANY, actions=mock.ANY)
        ])
        mock_br_int.add_flow.assert_called_once_with(
            table=0, priority=20, dl_dst=tap_flow['port_mac'],
            actions=mock.ANY
        )

    @mock.patch('neutron.plugins.ml2.drivers.openvswitch.agent.'
                'ovs_agent_extension_api.OVSAgentExtensionAPI')
    @mock.patch('neutron_taas.services.taas.drivers.linux.ovs_taas.'
                'OVSBridge_tap_extension')
    def test_delete_tap_flow(self, mock_tap_ext, mock_api):
        tap_flow = base.FAKE_TAP_FLOW

        mock_ovs_ext_api = mock_api.return_value
        mock_ovs_ext_api.request_int_br.return_value = FakeBridge('br_int')
        mock_ovs_ext_api.request_tun_br.return_value = FakeBridge('br_tun')

        obj, mock_tap_bridge, mock_br_int, mock_br_tun = \
            self._init_taas_driver(mock_ovs_ext_api, mock_tap_ext)
        self._vlidate_bridge_initialization(mock_ovs_ext_api, mock_tap_bridge,
                                            mock_br_int, mock_br_tun)

        mock_tap_bridge.reset_mock()
        mock_br_int.delete_flows.reset_mock()
        mock_br_tun.delete_flows.reset_mock()

        obj.delete_tap_flow(tap_flow)

        mock_tap_bridge.delete_flows.assert_not_called()
        mock_br_tun.delete_flows.assert_not_called()
        mock_br_int.delete_flows.assert_called_once_with(
            table=0, dl_dst=tap_flow['port_mac']
        )

    @mock.patch('neutron.plugins.ml2.drivers.openvswitch.agent.'
                'ovs_agent_extension_api.OVSAgentExtensionAPI')
    @mock.patch('neutron_taas.services.taas.drivers.linux.ovs_taas.'
                'OVSBridge_tap_extension')
    def test_create_tap_mirror_out_direction(self, mock_tap_ext, mock_api):
        tap_mirror = base.FAKE_TAP_MIRROR_OUT

        mock_ovs_ext_api = mock_api.return_value
        mock_ovs_ext_api.request_int_br.return_value = FakeBridge('br_int')
        mock_ovs_ext_api.request_tun_br.return_value = FakeBridge('br_tun')

        obj, mock_tap_bridge, mock_br_int, mock_br_tun = \
            self._init_taas_driver(mock_ovs_ext_api, mock_tap_ext)
        self._vlidate_bridge_initialization(mock_ovs_ext_api, mock_tap_bridge,
                                            mock_br_int, mock_br_tun)

        mock_tap_bridge.reset_mock()
        mock_br_int.add_flow.reset_mock()
        obj.create_tap_mirror(tap_mirror)

        mock_tap_bridge.add_flow.assert_has_calls([
            mock.call(table=taas_ovs_consts.TAAS_RECV_LOC, priority=20,
                      dl_src=tap_mirror['port']['mac_address'],
                      actions=mock.ANY),
            mock.call(table=taas_ovs_consts.TAAS_RECV_LOC, priority=1,
                      dl_dst=tap_mirror['port']['mac_address'],
                      actions=mock.ANY),
            mock.call(table=taas_ovs_consts.TAAS_RECV_REM, priority=1,
                      dl_dst=tap_mirror['port']['mac_address'],
                      actions=mock.ANY),
        ])
        mock_br_int.add_flow.assert_called_once_with(
            table=0, priority=20, in_port=mock.ANY, actions=mock.ANY
        )

    @mock.patch('neutron.plugins.ml2.drivers.openvswitch.agent.'
                'ovs_agent_extension_api.OVSAgentExtensionAPI')
    @mock.patch('neutron_taas.services.taas.drivers.linux.ovs_taas.'
                'OVSBridge_tap_extension')
    def test_create_tap_mirror_in_direction(self, mock_tap_ext, mock_api):
        tap_mirror = base.FAKE_TAP_MIRROR_IN

        mock_ovs_ext_api = mock_api.return_value
        mock_ovs_ext_api.request_int_br.return_value = FakeBridge('br_int')
        mock_ovs_ext_api.request_tun_br.return_value = FakeBridge('br_tun')

        obj, mock_tap_bridge, mock_br_int, mock_br_tun = \
            self._init_taas_driver(mock_ovs_ext_api, mock_tap_ext)
        self._vlidate_bridge_initialization(mock_ovs_ext_api, mock_tap_bridge,
                                            mock_br_int, mock_br_tun)

        mock_tap_bridge.reset_mock()
        mock_br_int.add_flow.reset_mock()
        obj.create_tap_mirror(tap_mirror)

        mock_tap_bridge.add_flow.assert_has_calls([
            mock.call(table=taas_ovs_consts.TAAS_RECV_LOC, priority=20,
                      dl_dst=tap_mirror['port']['mac_address'],
                      actions=mock.ANY),
            mock.call(table=taas_ovs_consts.TAAS_RECV_LOC, priority=1,
                      dl_dst=tap_mirror['port']['mac_address'],
                      actions=mock.ANY),
            mock.call(table=taas_ovs_consts.TAAS_RECV_REM, priority=1,
                      dl_dst=tap_mirror['port']['mac_address'],
                      actions=mock.ANY),
        ])
        mock_br_int.add_flow.assert_called_once_with(
            table=0, priority=20,
            dl_dst=base.FAKE_TAP_MIRROR_IN['port']['mac_address'],
            actions=mock.ANY
        )

    @mock.patch('neutron.plugins.ml2.drivers.openvswitch.agent.'
                'ovs_agent_extension_api.OVSAgentExtensionAPI')
    @mock.patch('neutron_taas.services.taas.drivers.linux.ovs_taas.'
                'OVSBridge_tap_extension')
    def test_delete_tap_mirror(self, mock_tap_ext, mock_api):
        tap_mirror = base.FAKE_TAP_MIRROR_OUT

        mock_ovs_ext_api = mock_api.return_value
        mock_ovs_ext_api.request_int_br.return_value = FakeBridge('br_int')
        mock_ovs_ext_api.request_tun_br.return_value = FakeBridge('br_tun')

        obj, mock_tap_bridge, mock_br_int, mock_br_tun = \
            self._init_taas_driver(mock_ovs_ext_api, mock_tap_ext)
        self._vlidate_bridge_initialization(mock_ovs_ext_api, mock_tap_bridge,
                                            mock_br_int, mock_br_tun)

        mock_tap_bridge.reset_mock()
        mock_br_int.delete_flows.reset_mock()

        obj.delete_tap_mirror(tap_mirror)

        mock_tap_bridge.delete_flows.assert_has_calls([
            mock.call(table=taas_ovs_consts.TAAS_RECV_REM,
                      dl_dst=tap_mirror['port']['mac_address']),
            mock.call(table=taas_ovs_consts.TAAS_RECV_LOC,
                      dl_dst=tap_mirror['port']['mac_address']),
            mock.call(table=taas_ovs_consts.TAAS_RECV_LOC,
                      dl_src=tap_mirror['port']['mac_address']),
        ])
        mock_br_int.delete_flows.assert_called_once()
