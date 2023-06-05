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
from webob import exc

from oslo_utils import uuidutils

from neutron.api import extensions
from neutron.conf import common as conf_common
from neutron.tests.unit.api.v2 import test_base as test_api_v2
from neutron.tests.unit.extensions import base as test_extensions_base

from neutron_lib.api.definitions import tap_mirror as tap_mirror_api

from neutron_taas import extensions as taas_extensions


TAP_MIRROR_PATH = 'taas/tap_mirrors'


class TapMirrorExtensionTestCase(test_extensions_base.ExtensionTestCase):

    def setUp(self):
        conf_common.register_core_common_config_opts()
        extensions.append_api_extensions_path(taas_extensions.__path__)
        super().setUp()
        plural_mappings = {'tap_mirror': 'tap_mirrors'}
        self.setup_extension(
            '%s.%s' % (taas_extensions.tap_mirror.TapMirrorBase.__module__,
                       taas_extensions.tap_mirror.TapMirrorBase.__name__),
            tap_mirror_api.ALIAS,
            taas_extensions.tap_mirror.Tap_mirror,
            'taas',
            plural_mappings=plural_mappings,
            translate_resource_name=False)
        self.instance = self.plugin.return_value

    def test_create_tap_mirror(self):
        project_id = uuidutils.generate_uuid()
        tap_mirror_data = {
            'project_id': project_id,
            'tenant_id': project_id,
            'name': 'MyMirror',
            'description': 'This is my Tap Mirror',
            'port_id': uuidutils.generate_uuid(),
            'directions': {"IN": 101},
            'remote_ip': '10.99.8.3',
            'mirror_type': 'gre',
        }
        data = {'tap_mirror': tap_mirror_data}
        expected_ret_val = copy.copy(tap_mirror_data)
        expected_ret_val.update({'id': uuidutils.generate_uuid()})
        self.instance.create_tap_mirror.return_value = expected_ret_val

        res = self.api.post(test_api_v2._get_path(TAP_MIRROR_PATH,
                                                  fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.instance.create_tap_mirror.assert_called_with(
            mock.ANY,
            tap_mirror=data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('tap_mirror', res)
        self.assertEqual(expected_ret_val, res['tap_mirror'])

    def test_delete_tap_mirror(self):
        self._test_entity_delete('tap_mirror')
