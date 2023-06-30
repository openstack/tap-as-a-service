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

import copy
from unittest import mock

from neutron.tests import base
from oslo_utils import uuidutils

from neutron_taas.services.taas.service_drivers.ovn import helper
from neutron_taas.services.taas.service_drivers.ovn import taas_ovn


class FakeMirrorContext():
    def __init__(self, tap_mirror):
        self._tap_mirror = tap_mirror

    @property
    def tap_mirror(self):
        return self._tap_mirror


class TestTaasOvnDriver(base.BaseTestCase):

    def setUp(self):
        super().setUp()
        self.driver = taas_ovn.TaasOvnDriver('tapmirror')
        add_req_thread = mock.patch.object(helper.TaasOvnProviderHelper,
                                           'add_request')
        self.mock_add_request = add_req_thread.start()
        helper_mock = mock.patch.object(helper.TaasOvnProviderHelper,
                                        'shutdown')
        helper_mock.start()

        self.tap_mirror_dict = {
            'mirror_type': 'gre',
            'directions': {'IN': 101},
            'id': uuidutils.generate_uuid(),
            'remote_ip': '10.92.10.5',
            'port_id': uuidutils.generate_uuid()
        }
        self.multi_dir_t_mirror = copy.deepcopy(self.tap_mirror_dict)
        self.multi_dir_t_mirror['directions'] = {'IN': 101, 'OUT': 102}

    def test_create_tap_mirror_postcommit(self):
        ctx = FakeMirrorContext(self.tap_mirror_dict)
        self.driver.create_tap_mirror_postcommit(ctx)
        expected_dict = {
            'type': 'mirror_add',
            'info': {
                'name': mock.ANY,
                'direction_filter': 'to-lport',
                'dest': self.tap_mirror_dict['remote_ip'],
                'mirror_type': self.tap_mirror_dict['mirror_type'],
                'index': self.tap_mirror_dict['directions']['IN'],
                'port_id': self.tap_mirror_dict['port_id'],
            }
        }
        self.mock_add_request.assert_called_once_with(expected_dict)

    def test_create_tap_mirror_postcommit_multi_dir(self):
        ctx = FakeMirrorContext(self.multi_dir_t_mirror)
        self.driver.create_tap_mirror_postcommit(ctx)

        expected_in_call = {
            'type': 'mirror_add',
            'info': {
                'name': mock.ANY,
                'direction_filter': 'to-lport',
                'dest': self.tap_mirror_dict['remote_ip'],
                'mirror_type': self.tap_mirror_dict['mirror_type'],
                'index': self.tap_mirror_dict['directions']['IN'],
                'port_id': self.tap_mirror_dict['port_id'],
            }
        }
        expected_out_call = copy.deepcopy(expected_in_call)
        expected_out_call['info']['direction_filter'] = 'from-lport'
        out_dir_tun_id = self.multi_dir_t_mirror['directions']['OUT']
        expected_out_call['info']['index'] = out_dir_tun_id

        expected_calls = [
            mock.call(expected_in_call),
            mock.call(expected_out_call)
        ]

        self.mock_add_request.assert_has_calls(expected_calls)

    def test_delete_tap_mirror_precommit(self):
        ctx = FakeMirrorContext(self.tap_mirror_dict)
        self.driver.delete_tap_mirror_precommit(ctx)

        expected_dict = {
            'type': 'mirror_del',
            'info': {
                'id': self.tap_mirror_dict['id'],
                'name': mock.ANY,
                'sink': self.tap_mirror_dict['remote_ip'],
                'port_id': self.tap_mirror_dict['port_id']}
        }
        self.mock_add_request.assert_called_once_with(expected_dict)

    def test_delete_tap_mirror_precommit_multi_dir(self):
        ctx = FakeMirrorContext(self.multi_dir_t_mirror)
        self.driver.delete_tap_mirror_precommit(ctx)

        expected_call = {
            'type': 'mirror_del',
            'info': {
                'id': self.tap_mirror_dict['id'],
                'name': mock.ANY,
                'sink': self.tap_mirror_dict['remote_ip'],
                'port_id': self.tap_mirror_dict['port_id'],
            }
        }

        expected_calls = [
            mock.call(expected_call),
            mock.call(expected_call)
        ]

        self.mock_add_request.assert_has_calls(expected_calls)
