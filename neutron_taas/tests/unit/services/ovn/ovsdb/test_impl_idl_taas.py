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

import os
from unittest import mock

from neutron.conf.plugins.ml2.drivers.ovn import ovn_conf
from neutron.tests import base
from ovs.db import idl as ovs_idl
from ovsdbapp.backend import ovs_idl as real_ovs_idl
from ovsdbapp.backend.ovs_idl import idlutils

from neutron_taas.services.taas.service_drivers.ovn.ovsdb import impl_idl_taas


basedir = os.path.dirname(os.path.abspath(__file__))
schema_files = {
    'OVN_Northbound': os.path.join(basedir,
                                   'schema_files', 'ovn-nb.ovsschema'),
}


class TestOvnNbIdlForTaas(base.BaseTestCase):

    def setUp(self):
        super().setUp()
        ovn_conf.register_opts()
        self.mock_gsh = mock.patch.object(
            idlutils, 'get_schema_helper',
            side_effect=lambda x, y: ovs_idl.SchemaHelper(
                location=schema_files['OVN_Northbound'])).start()
        self.idl_taas = impl_idl_taas.OvnNbIdlForTaas()

    def test__get_ovsdb_helper(self):
        self.mock_gsh.reset_mock()
        self.idl_taas._get_ovsdb_helper('foo')
        self.mock_gsh.assert_called_once_with('foo', 'OVN_Northbound')

    @mock.patch.object(real_ovs_idl.Backend, 'autocreate_indices', mock.Mock(),
                       create=True)
    def test_start(self):
        with mock.patch('ovsdbapp.backend.ovs_idl.connection.Connection',
                        side_effect=lambda x, timeout: mock.Mock()):
            idl_taas_1 = impl_idl_taas.OvnNbIdlForTaas()
            ret_taas_1 = idl_taas_1.start()
            id1 = id(ret_taas_1.ovsdb_connection)
            idl_taas_2 = impl_idl_taas.OvnNbIdlForTaas()
            ret_taas_2 = idl_taas_2.start()
            id2 = id(ret_taas_2.ovsdb_connection)
            self.assertNotEqual(id1, id2)

    @mock.patch('ovsdbapp.backend.ovs_idl.connection.Connection')
    def test_stop(self, mock_conn):
        mock_conn.stop.return_value = False
        with mock.patch.object(self.idl_taas, 'close') as mock_close:
            self.idl_taas.start()
            self.idl_taas.stop()
        mock_close.assert_called_once_with()

    @mock.patch('ovsdbapp.backend.ovs_idl.connection.Connection')
    def test_stop_no_connection(self, mock_conn):
        mock_conn.stop.return_value = False
        with mock.patch.object(self.idl_taas, 'close') as mock_close:
            self.idl_taas.stop()
        mock_close.assert_called_once_with()
