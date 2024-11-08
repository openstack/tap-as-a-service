# Copyright (C) 2015 Midokura SARL.
# All Rights Reserved.
#
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

from neutron_lib import constants
from neutron_lib import context
from neutron_lib.exceptions import taas as taas_exc
from neutron_lib import rpc as n_rpc
from neutron_lib.utils import net as n_utils
from oslo_config import cfg
from oslo_utils import uuidutils

from neutron.tests.unit import testlib_api

import neutron_taas.db.taas_db  # noqa
from neutron_taas.services.taas.service_drivers import taas_agent_api
from neutron_taas.services.taas.service_drivers import taas_rpc
from neutron_taas.services.taas import taas_plugin


class DummyError(Exception):
    pass


class TestTaasPlugin(testlib_api.SqlTestCase):
    def setUp(self):
        super().setUp()
        mock.patch.object(n_rpc, 'Connection', spec=object).start()
        mock.patch.object(taas_agent_api,
                          'TaasAgentApi', spec=object).start()
        self.driver = mock.MagicMock()
        mock.patch('neutron.services.service_base.load_drivers',
                   return_value=({'dummy_provider': self.driver},
                                 'dummy_provider')).start()
        mock.patch('neutron.db.servicetype_db.ServiceTypeManager.get_instance',
                   return_value=mock.MagicMock()).start()
        self._plugin = taas_plugin.TaasPlugin()
        self._context = context.get_admin_context()
        self.taas_cbs = taas_rpc.TaasCallbacks(self.driver, self._plugin)

        self._project_id = self._tenant_id = 'tenant-X'
        self._network_id = uuidutils.generate_uuid()
        self._host_id = 'host-A'
        self._port_id = uuidutils.generate_uuid()
        self._port_details = {
            'tenant_id': self._tenant_id,
            'binding:host_id': self._host_id,
            'mac_address': n_utils.get_random_mac(
                'fa:16:3e:00:00:00'.split(':')),
        }
        self._tap_service = {
            'tenant_id': self._tenant_id,
            'name': 'MyTap',
            'description': 'This is my tap service',
            'port_id': self._port_id,
            'project_id': self._project_id,
        }
        self.vlan_filter = "1-5,9,18,27-30,99-108,4000-4095"
        self._tap_flow = {
            'description': 'This is my tap flow',
            'direction': 'BOTH',
            'name': 'MyTapFlow',
            'source_port': self._port_id,
            'tenant_id': self._tenant_id,
            'project_id': self._project_id,
            'vlan_filter': self.vlan_filter,
        }

    @contextlib.contextmanager
    def tap_service(self):
        req = {
            'tap_service': self._tap_service,
        }
        with mock.patch.object(self._plugin, 'get_port_details',
                               return_value=self._port_details):
            self._plugin.create_tap_service(self._context, req)
        self._tap_service['id'] = mock.ANY
        self._tap_service['status'] = constants.DOWN

        self.driver.assert_has_calls([
            mock.call.create_tap_service_precommit(mock.ANY),
            mock.call.create_tap_service_postcommit(mock.ANY),
        ])
        pre_args = self.driver.create_tap_service_precommit.call_args[0][0]
        self.assertEqual(self._context, pre_args._plugin_context)
        self.assertEqual(self._tap_service, pre_args.tap_service)
        post_args = self.driver.create_tap_service_postcommit.call_args[0][0]
        self.assertEqual(self._context, post_args._plugin_context)
        self.assertEqual(self._tap_service, post_args.tap_service)
        self.taas_cbs.set_tap_service_status(
            self._context,
            {'id': pre_args.tap_service['id']},
            constants.ACTIVE, "dummyHost")
        self._tap_service['status'] = constants.ACTIVE
        yield self._plugin.get_tap_service(self._context,
                                           pre_args.tap_service['id'])

    @contextlib.contextmanager
    def tap_flow(self, tap_service, tenant_id=None):
        self._tap_flow['tap_service_id'] = tap_service
        if tenant_id is not None:
            self._tap_flow['tenant_id'] = tenant_id
        req = {
            'tap_flow': self._tap_flow,
        }
        with mock.patch.object(self._plugin, 'get_port_details',
                               return_value=self._port_details):
            self._plugin.create_tap_flow(self._context, req)
        self._tap_flow['id'] = mock.ANY
        self._tap_flow['status'] = constants.DOWN
        self._tap_service['id'] = mock.ANY
        self._tap_flow['vlan_filter'] = mock.ANY

        self.driver.assert_has_calls([
            mock.call.create_tap_flow_precommit(mock.ANY),
            mock.call.create_tap_flow_postcommit(mock.ANY),
        ])
        pre_args = self.driver.create_tap_flow_precommit.call_args[0][0]
        self.assertEqual(self._context, pre_args._plugin_context)
        self.assertEqual(self._tap_flow, pre_args.tap_flow)
        post_args = self.driver.create_tap_flow_postcommit.call_args[0][0]
        self.assertEqual(self._context, post_args._plugin_context)
        self.assertEqual(self._tap_flow, post_args.tap_flow)
        self.taas_cbs.set_tap_flow_status(
            self._context,
            {'id': pre_args.tap_flow['id']},
            constants.ACTIVE, "dummyHost")
        self._tap_flow['status'] = constants.ACTIVE
        yield self._plugin.get_tap_flow(self._context,
                                        pre_args.tap_flow['id'])

    def test_create_tap_service(self):
        with self.tap_service():
            pass

    def test_verify_taas_id_reused(self):
        # make small range id
        cfg.CONF.set_override("vlan_range_start", 1, group="taas")
        cfg.CONF.set_override("vlan_range_end", 3, group="taas")
        with self.tap_service() as ts_1, self.tap_service() as ts_2, \
                self.tap_service() as ts_3, self.tap_service() as ts_4:
            ts_id_1 = ts_1['id']
            ts_id_2 = ts_2['id']
            ts_id_3 = ts_3['id']
            tap_id_assoc_1 = self._plugin.create_tap_id_association(
                self._context, ts_id_1)
            tap_id_assoc_2 = self._plugin.create_tap_id_association(
                self._context, ts_id_2)
            self.assertEqual({1, 2}, {tap_id_assoc_1['taas_id'],
                             tap_id_assoc_2['taas_id']})
            with testtools.ExpectedException(taas_exc.TapServiceLimitReached):
                self._plugin.create_tap_id_association(
                    self._context,
                    ts_4['id']
                )
            # free an tap_id and verify could reallocate same taas id
            self._plugin.delete_tap_service(self._context, ts_id_1)
            self.taas_cbs.set_tap_service_status(self._context,
                                                 {'id': ts_id_1},
                                                 constants.INACTIVE,
                                                 "dummyHost")
            tap_id_assoc_3 = self._plugin.create_tap_id_association(
                self._context, ts_id_3)
            self.assertEqual({1, 2}, {tap_id_assoc_3['taas_id'],
                             tap_id_assoc_2['taas_id']})

    def test_create_tap_service_wrong_tenant_id(self):
        self._port_details['tenant_id'] = 'other-tenant'
        with testtools.ExpectedException(taas_exc.PortDoesNotBelongToTenant), \
                self.tap_service():
            pass
        self.assertEqual([], self.driver.mock_calls)

    def test_create_tap_service_reach_limit(self):
        # TODO(Yoichiro):Need to move this test to taas_rpc test
        pass

    def test_create_tap_service_failed_on_service_driver(self):
        attr = {'create_tap_service_postcommit.side_effect': DummyError}
        self.driver.configure_mock(**attr)
        with testtools.ExpectedException(DummyError):
            req = {
                'tap_service': self._tap_service,
            }
            with mock.patch.object(self._plugin, 'get_port_details',
                                   return_value=self._port_details):
                self._plugin.create_tap_service(self._context, req)

    def test_delete_tap_service(self):
        with self.tap_service() as ts:
            self._plugin.delete_tap_service(self._context, ts['id'])
            self._tap_service['id'] = ts['id']
        self.driver.assert_has_calls([
            mock.call.delete_tap_service_precommit(mock.ANY),
        ])
        self._tap_service['status'] = constants.PENDING_DELETE
        pre_args = self.driver.delete_tap_service_precommit.call_args[0][0]
        self.assertEqual(self._context, pre_args._plugin_context)
        self.assertEqual(self._tap_service, pre_args.tap_service)
        self.taas_cbs.set_tap_service_status(self._context,
                                             {'id': self._tap_service['id']},
                                             constants.INACTIVE,
                                             "dummyHost")

    def test_delete_tap_service_with_flow(self):
        with self.tap_service() as ts, \
                self.tap_flow(tap_service=ts['id']) as tf:
            self._plugin.delete_tap_service(self._context, ts['id'])
            self._tap_service['id'] = ts['id']
            self._tap_flow['id'] = tf['id']
        self.driver.assert_has_calls([
            mock.call.delete_tap_flow_precommit(mock.ANY),
            mock.call.delete_tap_service_precommit(mock.ANY),
        ])
        self._tap_service['status'] = constants.PENDING_DELETE
        self._tap_flow['status'] = constants.PENDING_DELETE
        pre_args = self.driver.delete_tap_flow_precommit.call_args[0][0]
        self.assertEqual(self._context, pre_args._plugin_context)
        self.assertEqual(self._tap_flow, pre_args.tap_flow)
        pre_args = self.driver.delete_tap_service_precommit.call_args[0][0]
        self.assertEqual(self._context, pre_args._plugin_context)
        self.assertEqual(self._tap_service, pre_args.tap_service)
        self.taas_cbs.set_tap_flow_status(self._context,
                                          {'id': self._tap_flow['id']},
                                          constants.INACTIVE,
                                          "dummyHost")
        self.taas_cbs.set_tap_service_status(self._context,
                                             {'id': self._tap_service['id']},
                                             constants.INACTIVE,
                                             "dummyHost")

    def test_delete_tap_service_non_existent(self):
        with testtools.ExpectedException(taas_exc.TapServiceNotFound):
            self._plugin.delete_tap_service(self._context, 'non-existent')

    def test_create_tap_flow(self):
        with self.tap_service() as ts, self.tap_flow(tap_service=ts['id']):
            pass

    def test_create_tap_flow_wrong_tenant_id(self):
        with self.tap_service() as ts, \
                testtools.ExpectedException(
                    taas_exc.TapServiceNotBelongToTenant), \
                self.tap_flow(tap_service=ts['id'], tenant_id='other-tenant'):
            pass

    def test_create_tap_flow_failed_on_service_driver(self):
        with self.tap_service() as ts:
            attr = {'create_tap_flow_postcommit.side_effect': DummyError}
            self.driver.configure_mock(**attr)
            with testtools.ExpectedException(DummyError):
                self._tap_flow['tap_service_id'] = ts['id']
                req = {
                    'tap_flow': self._tap_flow,
                }
                with mock.patch.object(self._plugin, 'get_port_details',
                                       return_value=self._port_details):
                    self._plugin.create_tap_flow(self._context, req)

    def test_delete_tap_flow(self):
        with self.tap_service() as ts, \
                self.tap_flow(tap_service=ts['id']) as tf:
            self._plugin.delete_tap_flow(self._context, tf['id'])
            self._tap_flow['id'] = tf['id']
        self.driver.assert_has_calls([
            mock.call.delete_tap_flow_precommit(mock.ANY),
        ])
        self._tap_flow['status'] = constants.PENDING_DELETE
        pre_args = self.driver.delete_tap_flow_precommit.call_args[0][0]
        self.assertEqual(self._context, pre_args._plugin_context)
        self.assertEqual(self._tap_flow, pre_args.tap_flow)
        self.taas_cbs.set_tap_flow_status(self._context,
                                          {'id': self._tap_flow['id']},
                                          constants.INACTIVE,
                                          "dummyHost")
