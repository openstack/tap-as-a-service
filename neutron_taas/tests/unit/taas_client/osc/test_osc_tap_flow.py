# All Rights Reserved 2020
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

import copy
import operator
from unittest import mock

from neutronclient.tests.unit.osc.v2 import fakes as test_fakes
from osc_lib import utils as osc_utils
from osc_lib.utils import columns as column_util
from oslo_utils import uuidutils

from neutron_taas.taas_client.osc import tap_flow as osc_tap_flow
from neutron_taas.tests.unit.taas_client.osc import fakes


columns_long = tuple(col for col, _, listing_mode in osc_tap_flow._attr_map
                     if listing_mode in (column_util.LIST_BOTH,
                                         column_util.LIST_LONG_ONLY))
headers_long = tuple(head for _, head, listing_mode in
                     osc_tap_flow._attr_map if listing_mode in
                     (column_util.LIST_BOTH, column_util.LIST_LONG_ONLY))
sorted_attr_map = sorted(osc_tap_flow._attr_map, key=operator.itemgetter(1))
sorted_columns = tuple(col for col, _, _ in sorted_attr_map)
sorted_headers = tuple(head for _, head, _ in sorted_attr_map)


def _get_data(attrs, columns=sorted_columns):
    return osc_utils.get_dict_properties(attrs, columns)


class TestCreateTapService(test_fakes.TestNeutronClientOSCV2):

    columns = (
        'Direction',
        'ID',
        'Name',
        'Status',
        'Tenant',
        'source_port',
        'tap_service_id',
    )

    def setUp(self):
        super(TestCreateTapService, self).setUp()
        self.cmd = osc_tap_flow.CreateTapFlow(self.app, self.namespace)

    def test_create_tap_flow(self):
        """Test Create Tap Flow."""
        fake_tap_flow = fakes.FakeTapFlow.create_tap_flow(
            attrs={
                'source_port': uuidutils.generate_uuid(),
                'tap_service_id': uuidutils.generate_uuid()
            }
        )

        self.neutronclient.post = mock.Mock(
            return_value={osc_tap_flow.TAP_FLOW: fake_tap_flow})
        arg_list = [
            '--name', fake_tap_flow['name'],
            '--port', fake_tap_flow['source_port'],
            '--tap-service', fake_tap_flow['tap_service_id'],
            '--direction', fake_tap_flow['direction'],
        ]

        verify_list = [
            ('name', fake_tap_flow['name']),
            ('port', fake_tap_flow['source_port']),
            ('tap_service', fake_tap_flow['tap_service_id']),
        ]

        parsed_args = self.check_parser(self.cmd, arg_list, verify_list)
        with mock.patch.object(self.neutronclient, 'find_resource') as nc_find:
            nc_find.side_effect = [
                {'id': fake_tap_flow['source_port']},
                {'id': fake_tap_flow['tap_service_id']}
            ]

            columns, data = self.cmd.take_action(parsed_args)
            self.neutronclient.post.assert_called_once_with(
                '/taas/tap_flows',
                body={
                    osc_tap_flow.TAP_FLOW:
                        {
                            'name': fake_tap_flow['name'],
                            'source_port': fake_tap_flow['source_port'],
                            'tap_service_id': fake_tap_flow['tap_service_id'],
                            'direction': fake_tap_flow['direction']
                        }
                }
            )
            self.assertEqual(self.columns, columns)
            self.assertItemEqual(_get_data(fake_tap_flow), data)


class TestListTapFlow(test_fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestListTapFlow, self).setUp()
        self.cmd = osc_tap_flow.ListTapFlow(self.app, self.namespace)

    def test_list_tap_flows(self):
        """Test List Tap Flow."""
        fake_tap_flows = fakes.FakeTapFlow.create_tap_flows(
            attrs={
                'source_port': uuidutils.generate_uuid(),
                'tap_service_id': uuidutils.generate_uuid(),
            },
            count=2)
        self.neutronclient.list = mock.Mock(return_value=fake_tap_flows)
        arg_list = []
        verify_list = []

        parsed_args = self.check_parser(self.cmd, arg_list, verify_list)

        headers, data = self.cmd.take_action(parsed_args)

        self.neutronclient.list.assert_called_once()
        self.assertEqual(headers, list(headers_long))
        self.assertListItemEqual(
            list(data),
            [_get_data(fake_tap_flow, columns_long) for fake_tap_flow
             in fake_tap_flows[osc_tap_flow.TAP_FLOWS]]
        )


class TestDeleteTapFlow(test_fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestDeleteTapFlow, self).setUp()
        self.neutronclient.find_resource = mock.Mock(
            side_effect=lambda _, name_or_id: {'id': name_or_id})
        self.cmd = osc_tap_flow.DeleteTapFlow(self.app, self.namespace)

    def test_delete_tap_flow(self):
        """Test Delete tap flow."""

        fake_tap_flow = fakes.FakeTapFlow.create_tap_flow(
            attrs={
                'source_port': uuidutils.generate_uuid(),
                'tap_service_id': uuidutils.generate_uuid(),
            }
        )
        self.neutronclient.delete = mock.Mock()

        arg_list = [
            fake_tap_flow['id'],
        ]
        verify_list = [
            (osc_tap_flow.TAP_FLOW, [fake_tap_flow['id']]),
        ]

        parsed_args = self.check_parser(self.cmd, arg_list, verify_list)

        result = self.cmd.take_action(parsed_args)

        self.neutronclient.delete.assert_called_once_with(
            osc_tap_flow.resource_path % ('tap_flows',
                                          fake_tap_flow['id']))
        self.assertIsNone(result)


class TestShowTapFlow(test_fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestShowTapFlow, self).setUp()
        self.neutronclient.find_resource = mock.Mock(
            side_effect=lambda _, name_or_id: {'id': name_or_id})
        self.cmd = osc_tap_flow.ShowTapFlow(self.app, self.namespace)

    def test_show_tap_flow(self):
        """Test Show tap flow."""

        fake_tap_flow = fakes.FakeTapFlow.create_tap_flow(
            attrs={
                'source_port': uuidutils.generate_uuid(),
                'tap_service_id': uuidutils.generate_uuid(),
            }
        )
        self.neutronclient.get = mock.Mock(
            return_value={osc_tap_flow.TAP_FLOW: fake_tap_flow})
        arg_list = [
            fake_tap_flow['id'],
        ]
        verify_list = [
            (osc_tap_flow.TAP_FLOW, fake_tap_flow['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arg_list, verify_list)

        headers, data = self.cmd.take_action(parsed_args)

        self.neutronclient.get.assert_called_once_with(
            osc_tap_flow.resource_path % ('tap_flows',
                                          fake_tap_flow['id']))
        self.assertEqual(sorted_headers, headers)
        self.assertItemEqual(_get_data(fake_tap_flow), data)


class TestUpdateTapFlow(test_fakes.TestNeutronClientOSCV2):

    _new_name = 'new_name'

    columns = (
        'Direction',
        'ID',
        'Name',
        'Status',
        'Tenant',
        'source_port',
        'tap_service_id',
    )

    def setUp(self):
        super(TestUpdateTapFlow, self).setUp()
        self.cmd = osc_tap_flow.UpdateTapFlow(self.app, self.namespace)
        self.neutronclient.find_resource = mock.Mock(
            side_effect=lambda _, name_or_id: {'id': name_or_id})

    def test_update_tap_flow(self):
        """Test update tap service"""
        fake_tap_flow = fakes.FakeTapFlow.create_tap_flow(
            attrs={
                'source_port': uuidutils.generate_uuid(),
                'tap_service_id': uuidutils.generate_uuid(),
            }
        )
        new_tap_flow = copy.deepcopy(fake_tap_flow)
        new_tap_flow['name'] = self._new_name

        self.neutronclient.put = mock.Mock(
            return_value={osc_tap_flow.TAP_FLOW: new_tap_flow})

        arg_list = [
            fake_tap_flow['id'],
            '--name', self._new_name,
        ]
        verify_list = [('name', self._new_name)]

        parsed_args = self.check_parser(self.cmd, arg_list, verify_list)
        columns, data = self.cmd.take_action(parsed_args)
        attrs = {'name': self._new_name}

        self.neutronclient.put.assert_called_once_with(
            osc_tap_flow.resource_path % ('tap_flows',
                                          new_tap_flow['id']),
            {osc_tap_flow.TAP_FLOW: attrs})
        self.assertEqual(self.columns, columns)
        self.assertItemEqual(_get_data(new_tap_flow), data)
