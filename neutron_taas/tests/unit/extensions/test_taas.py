# Copyright 2017 FUJITSU LABORATORIES LTD.

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at

#         http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
from unittest import mock
from webob import exc

from oslo_utils import uuidutils

from neutron.api import extensions
from neutron.conf import common as conf_common
from neutron.tests.unit.api.v2 import test_base as test_api_v2
from neutron.tests.unit.extensions import base as test_extensions_base
from neutron_lib.api.definitions import taas as taas_api

from neutron_taas import extensions as taas_extensions

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path

TAP_SERVICE_PATH = 'taas/tap_services'
TAP_FLOW_PATH = 'taas/tap_flows'


class TaasExtensionTestCase(test_extensions_base.ExtensionTestCase):

    def setUp(self):
        conf_common.register_core_common_config_opts()
        extensions.append_api_extensions_path(taas_extensions.__path__)
        super(TaasExtensionTestCase, self).setUp()
        plural_mappings = {'tap_service': 'tap_services',
                           'tap_flow': 'tap_flows'}
        self.setup_extension(
            '%s.%s' % (taas_extensions.taas.TaasPluginBase.__module__,
                       taas_extensions.taas.TaasPluginBase.__name__),
            taas_api.ALIAS,
            taas_extensions.taas.Taas,
            'taas',
            plural_mappings=plural_mappings,
            translate_resource_name=False)
        self.instance = self.plugin.return_value

    def test_create_tap_service(self):
        tenant_id = _uuid()
        tap_service_data = {
            'tenant_id': tenant_id,
            'name': 'MyTap',
            'description': 'This is my tap service',
            'port_id': _uuid(),
            'project_id': tenant_id,
        }
        data = {'tap_service': tap_service_data}
        expected_ret_val = copy.copy(data['tap_service'])
        expected_ret_val.update({'id': _uuid()})
        instance = self.plugin.return_value
        self.instance.create_tap_service.return_value = expected_ret_val

        res = self.api.post(_get_path(TAP_SERVICE_PATH, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        instance.create_tap_service.assert_called_with(
            mock.ANY,
            tap_service=data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('tap_service', res)
        self.assertEqual(expected_ret_val, res['tap_service'])

    def test_delete_tap_service(self):
        self._test_entity_delete('tap_service')

    def _get_expected_tap_flow(self, data):
        return data

    def test_create_tap_flow(self):
        tenant_id = _uuid()
        tap_flow_data = {
            'tenant_id': tenant_id,
            'name': 'MyTapFlow',
            'description': 'This is my tap flow',
            'direction': 'BOTH',
            'tap_service_id': _uuid(),
            'source_port': _uuid(),
            'project_id': tenant_id,
        }
        data = {'tap_flow': tap_flow_data}
        expected_data = self._get_expected_tap_flow(data)
        expected_ret_val = copy.copy(expected_data['tap_flow'])
        expected_ret_val.update({'id': _uuid()})
        instance = self.plugin.return_value
        instance.create_tap_flow.return_value = expected_ret_val

        res = self.api.post(_get_path(TAP_FLOW_PATH, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        instance.create_tap_flow.assert_called_with(
            mock.ANY,
            tap_flow=expected_data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('tap_flow', res)
        self.assertEqual(expected_ret_val, res['tap_flow'])

    def test_delete_tap_flow(self):
        self._test_entity_delete('tap_flow')
