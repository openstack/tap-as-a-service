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

from neutron.tests.unit import testlib_api

from neutron_lib import context
from neutron_lib.exceptions import taas as taas_exc

from oslo_utils import importutils
from oslo_utils import uuidutils

from neutron_taas.db import tap_mirror_db


DB_PLUGIN_KLAAS = 'neutron.db.db_base_plugin_v2.NeutronDbPluginV2'
_uuid = uuidutils.generate_uuid


class TapMirrorDbTestCase(testlib_api.SqlTestCase):

    """Unit test for Tap Mirror DB support."""

    def setUp(self):
        super().setUp()
        self.ctx = context.get_admin_context()
        self.db_mixin = tap_mirror_db.Taas_mirror_db_mixin()
        self.plugin = importutils.import_object(DB_PLUGIN_KLAAS)
        self.project_id = 'fake-project-id'

    def _get_tap_mirror_data(self, name='tm-1', port_id=None,
                             directions='{"IN": "99"}', remote_ip='10.99.8.3',
                             mirror_type='erspanv1'):
        port_id = port_id or _uuid()
        return {"tap_mirror": {"name": name,
                               "project_id": self.project_id,
                               "description": "test tap mirror",
                               "port_id": port_id,
                               'directions': directions,
                               'remote_ip': remote_ip,
                               'mirror_type': mirror_type
                               }
                }

    def _get_tap_mirror(self, tap_mirror_id):
        """Helper method to retrieve tap Mirror."""
        with self.ctx.session.begin():
            return self.db_mixin.get_tap_mirror(self.ctx, tap_mirror_id)

    def _get_tap_mirrors(self):
        """Helper method to retrieve all tap Mirror."""
        with self.ctx.session.begin():
            return self.db_mixin.get_tap_mirrors(self.ctx)

    def _create_tap_mirror(self, tap_mirror):
        """Helper method to create tap Mirror."""
        with self.ctx.session.begin():
            return self.db_mixin.create_tap_mirror(self.ctx, tap_mirror)

    def _update_tap_mirror(self, tap_mirror_id, tap_mirror):
        """Helper method to update tap Mirror."""
        with self.ctx.session.begin():
            return self.db_mixin.update_tap_mirror(self.ctx,
                                                   tap_mirror_id,
                                                   tap_mirror)

    def _delete_tap_mirror(self, tap_mirror_id):
        """Helper method to delete tap Mirror."""
        with self.ctx.session.begin():
            return self.db_mixin.delete_tap_mirror(self.ctx, tap_mirror_id)

    def test_tap_mirror_get(self):
        name = 'test-tap-mirror'
        data = self._get_tap_mirror_data(name=name)
        result = self._create_tap_mirror(data)
        get_result = self._get_tap_mirror(result['id'])
        self.assertEqual(name, get_result['name'])

    def test_tap_mirror_create(self):
        name = 'test-tap-mirror'
        port_id = _uuid()
        data = self._get_tap_mirror_data(name=name, port_id=port_id)
        result = self._create_tap_mirror(data)
        self.assertEqual(name, result['name'])
        self.assertEqual(port_id, result['port_id'])

    def test_tap_mirror_list(self):
        name_1 = "tm-1"
        data_1 = self._get_tap_mirror_data(name=name_1)
        name_2 = "tm-2"
        data_2 = self._get_tap_mirror_data(name=name_2)
        self._create_tap_mirror(data_1)
        self._create_tap_mirror(data_2)
        tap_mirrors = self._get_tap_mirrors()
        self.assertEqual(2, len(tap_mirrors))

    def test_tap_mirror_update(self):
        original_name = "tm-1"
        updated_name = "tm-1-got-updated"
        data = self._get_tap_mirror_data(name=original_name)
        tm = self._create_tap_mirror(data)
        updated_data = self._get_tap_mirror_data(name=updated_name)
        tm_updated = self._update_tap_mirror(tm['id'], updated_data)
        self.assertEqual(updated_name, tm_updated['name'])

    def test_tap_mirror_delete(self):
        data = self._get_tap_mirror_data()
        result = self._create_tap_mirror(data)
        self._delete_tap_mirror(result['id'])
        self.assertRaises(taas_exc.TapMirrorNotFound,
                          self._get_tap_mirror, result['id'])
