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

import contextlib

import testtools
from unittest import mock

from neutron.tests.unit import testlib_api
from neutron_lib import context
from neutron_lib.exceptions import taas as taas_exc
from neutron_lib import rpc as n_rpc
from neutron_lib.utils import net as n_utils
from oslo_utils import uuidutils

from neutron_taas.services.taas import tap_mirror_plugin


class TestTapMirrorPlugin(testlib_api.SqlTestCase):
    def setUp(self):
        super().setUp()
        mock.patch.object(n_rpc, 'Connection', spec=object).start()

        self.driver = mock.MagicMock()
        mock.patch('neutron.services.service_base.load_drivers',
                   return_value=({'dummy_provider': self.driver},
                                 'dummy_provider')).start()
        mock.patch('neutron.db.servicetype_db.ServiceTypeManager.get_instance',
                   return_value=mock.MagicMock()).start()
        self._plugin = tap_mirror_plugin.TapMirrorPlugin()
        self._context = context.get_admin_context()

        self._project_id = self._tenant_id = uuidutils.generate_uuid()
        self._network_id = uuidutils.generate_uuid()
        self._host_id = 'host-A'
        self._port_id = uuidutils.generate_uuid()
        self._port_details = {
            'tenant_id': self._tenant_id,
            'binding:host_id': self._host_id,
            'mac_address': n_utils.get_random_mac(
                'fa:16:3e:00:00:00'.split(':')),
        }
        self._tap_mirror = {
            'project_id': self._project_id,
            'tenant_id': self._tenant_id,
            'name': 'MyMirror',
            'description': 'This is my Tap Mirror',
            'port_id': self._port_id,
            'directions': {"IN": 101},
            'remote_ip': '10.99.8.3',
            'mirror_type': 'gre',
        }

    @contextlib.contextmanager
    def tap_mirror(self, **kwargs):
        self._tap_mirror.update(kwargs)
        req = {
            'tap_mirror': self._tap_mirror,
        }
        with mock.patch.object(self._plugin, 'get_port_details',
                               return_value=self._port_details):
            mirror = self._plugin.create_tap_mirror(self._context, req)
        self._tap_mirror['id'] = mock.ANY

        self.driver.assert_has_calls([
            mock.call.create_tap_mirror_precommit(mock.ANY),
            mock.call.create_tap_mirror_postcommit(mock.ANY),
        ])
        pre_call_args = self.driver.create_tap_mirror_precommit.call_args[0][0]
        self.assertEqual(self._context, pre_call_args._plugin_context)
        self.assertEqual(self._tap_mirror, pre_call_args.tap_mirror)

        post_call_args = self.driver.create_tap_mirror_postcommit.call_args
        post_call_args = post_call_args[0][0]
        self.assertEqual(self._context, post_call_args._plugin_context)
        self.assertEqual(self._tap_mirror, post_call_args.tap_mirror)

        yield self._plugin.get_tap_mirror(self._context,
                                          mirror['id'])

    def test_create_tap_mirror(self):
        with self.tap_mirror():
            pass

    def test_create_tap_mirror_wrong_project_id(self):
        self._port_details['project_id'] = 'other-tenant'
        self._port_details['tenant_id'] = 'other-tenant'
        with testtools.ExpectedException(taas_exc.PortDoesNotBelongToTenant), \
                self.tap_mirror():
            pass
        self.assertEqual([], self.driver.mock_calls)

    def test_create_duplicate_tunnel_id(self):
        with self.tap_mirror() as tm1:
            with mock.patch.object(self._plugin, 'get_tap_mirrors',
                                   return_value=[tm1]):
                with testtools.ExpectedException(
                        taas_exc.TapMirrorTunnelConflict), \
                        self.tap_mirror(directions={"IN": 101}):
                    pass

    def test_create_different_tunnel_id(self):
        with self.tap_mirror() as tm1:
            with mock.patch.object(self._plugin, 'get_tap_mirrors',
                                   return_value=[tm1]):
                with self.tap_mirror(directions={"IN": 102}):
                    pass

    def test_same_tunnel_id_different_direction(self):
        with self.tap_mirror() as tm1:
            with mock.patch.object(self._plugin, 'get_tap_mirrors',
                                   return_value=[tm1]):
                with testtools.ExpectedException(
                        taas_exc.TapMirrorTunnelConflict), \
                        self.tap_mirror(directions={"OUT": 101}):
                    pass

    def test_two_direction_tunnel_id(self):
        with self.tap_mirror(directions={'IN': 101, 'OUT': 102}) as tm1:
            with mock.patch.object(self._plugin, 'get_tap_mirrors',
                                   return_value=[tm1]):
                with testtools.ExpectedException(
                        taas_exc.TapMirrorTunnelConflict), \
                        self.tap_mirror(directions={"OUT": 101}):
                    pass

    def test_delete_tap_mrror(self):
        with self.tap_mirror() as tm:
            self._plugin.delete_tap_mirror(self._context, tm['id'])
            self._tap_mirror['id'] = tm['id']

    def test_delete_tap_mirror_non_existent(self):
        with testtools.ExpectedException(taas_exc.TapMirrorNotFound):
            self._plugin.delete_tap_mirror(self._context, 'non-existent')
