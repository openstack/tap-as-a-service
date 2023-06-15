# Copyright (C) 2018 AT&T
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

import copy

from oslotest import base


FAKE_PORT_PARAMS = {
    'mac': '52:54:00:12:35:02', 'pci_slot': 3, 'vf_index': '89',
    'pf_device': 'net_enp0s3_52_54_00_12_35_02', 'src_vlans': '20'}

FAKE_TAP_SERVICE = {
    'taas_id': '1234',
    'port': {
        'id': 'fake_1',
        'mac_address': "52:54:00:12:35:02",
        'binding:profile': {'pci_slot': 3},
        'binding:vif_details': {'vlan': '20'}
    }
}

FAKE_OF_PORT = {
    'port_name': 'tap4321',
    'ofport': 12,
}
FAKE_PORT_DICT = {
    FAKE_OF_PORT['port_name']: 4
}
FAKE_TAP_SERVICE_OVS = {
    'taas_id': 4321,
    'port': {
        'id': 'fake_2',
        'mac_address': "fa:16:3e:33:0e:d4",
        'binding:profile': {},
        'binding:vif_details': {
            'connectivity': 'l2',
            'port_filter': True,
            'ovs_hybrid_plug': False,
            'datapath_type': 'system',
            'bridge_name': 'br-int'
        }
    }
}

FAKE_TAP_FLOW = {
    'taas_id': FAKE_TAP_SERVICE_OVS['taas_id'],
    'port': FAKE_TAP_SERVICE['port'],
    'port_mac': 'fa:16:3e:5c:67:6a',
    'ts_port': FAKE_TAP_SERVICE['port'],
    'source_vlans_list': ['4-6', '8-10', '15-18,20'],
    'vlan_filter_list': '1-5,9,18,20,27-30,4000-4095',
    'tap_flow': {
        'direction': 'IN', 'vlan_filter': '20'
    }
}


FAKE_TAP_MIRROR_OUT = {
    'tap_mirror': {
        'id': 'mirror_uuid',
        'port_id': 'port_uuid',
        'directions': {'OUT': '102'},
        'remote_ip': '100.109.0.48',
        'mirror_type': 'gre',
    },
    'port': {
        'id': 'port_uuid',
        'mac_address': 'fa:16:3e:69:0e:f3',
    }
}

FAKE_TAP_MIRROR_IN = copy.deepcopy(FAKE_TAP_MIRROR_OUT)
FAKE_TAP_MIRROR_IN['tap_mirror']['directions'] = {'IN': '101'}


class TaasTestCase(base.BaseTestCase):
    """Test case base class for all unit tests."""
