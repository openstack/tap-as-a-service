# Copyright (c) 2025 Red Hat Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_policy import policy

from neutron import policy as neutron_policy
from neutron.tests.unit.conf.policies import test_base


class TapMirrorAPITestCase(test_base.PolicyBaseTestCase):

    def setUp(self):
        super().setUp()
        self.target = {
            'project_id': self.project_id,
            'tenant_id': self.project_id
        }
        self.alt_target = {
            'project_id': self.alt_project_id,
            'tenant_id': self.alt_project_id
        }


class SystemAdminTests(TapMirrorAPITestCase):

    def setUp(self):
        super().setUp()
        self.context = self.system_admin_ctx

    def test_create_tap_mirror(self):
        self.assertRaises(
            policy.InvalidScope,
            neutron_policy.enforce, self.context, 'create_tap_mirror',
            self.target)
        self.assertRaises(
            policy.InvalidScope,
            neutron_policy.enforce, self.context, 'create_tap_mirror',
            self.alt_target)

    def test_update_tap_mirror(self):
        self.assertRaises(
            policy.InvalidScope,
            neutron_policy.enforce, self.context, 'update_tap_mirror',
            self.target)
        self.assertRaises(
            policy.InvalidScope,
            neutron_policy.enforce, self.context, 'update_tap_mirror',
            self.alt_target)

    def test_get_tap_mirror(self):
        self.assertRaises(
            policy.InvalidScope,
            neutron_policy.enforce, self.context, 'get_tap_mirror',
            self.target)
        self.assertRaises(
            policy.InvalidScope,
            neutron_policy.enforce, self.context, 'get_tap_mirror',
            self.alt_target)

    def test_delete_tap_mirror(self):
        self.assertRaises(
            policy.InvalidScope,
            neutron_policy.enforce, self.context, 'delete_tap_mirror',
            self.target)
        self.assertRaises(
            policy.InvalidScope,
            neutron_policy.enforce, self.context, 'delete_tap_mirror',
            self.alt_target)


class SystemMemberTests(SystemAdminTests):

    def setUp(self):
        super().setUp()
        self.context = self.system_member_ctx


class SystemReaderTests(SystemMemberTests):

    def setUp(self):
        super().setUp()
        self.context = self.system_reader_ctx


class AdminTests(TapMirrorAPITestCase):

    def setUp(self):
        super().setUp()
        self.context = self.project_admin_ctx

    def test_create_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(
                self.context, 'create_tap_mirror', self.target))
        self.assertTrue(
            neutron_policy.enforce(
                self.context, 'create_tap_mirror', self.alt_target))

    def test_update_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(
                self.context, 'update_tap_mirror', self.target))
        self.assertTrue(
            neutron_policy.enforce(
                self.context, 'update_tap_mirror', self.alt_target))

    def test_get_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(
                self.context, 'get_tap_mirror', self.target))
        self.assertTrue(
            neutron_policy.enforce(
                self.context, 'get_tap_mirror', self.alt_target))

    def test_delete_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(
                self.context, 'delete_tap_mirror', self.target))
        self.assertTrue(
            neutron_policy.enforce(
                self.context, 'delete_tap_mirror', self.alt_target))


class ProjectManagerTests(TapMirrorAPITestCase):

    def setUp(self):
        super().setUp()
        self.context = self.project_manager_ctx

    def test_create_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(self.context, 'create_tap_mirror',
            self.target))
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'create_tap_mirror',
            self.alt_target)

    def test_update_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(self.context, 'update_tap_mirror',
            self.target))
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'update_tap_mirror',
            self.alt_target)

    def test_get_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(self.context, 'get_tap_mirror',
            self.target))
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'get_tap_mirror',
            self.alt_target)

    def test_delete_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(self.context, 'delete_tap_mirror',
            self.target))
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'delete_tap_mirror',
            self.alt_target)


class ProjectMemberTests(ProjectManagerTests):

    def setUp(self):
        super().setUp()
        self.context = self.project_member_ctx


class ProjectReaderTests(TapMirrorAPITestCase):

    def setUp(self):
        super().setUp()
        self.context = self.project_reader_ctx

    def test_create_tap_mirror(self):
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'create_tap_mirror',
            self.target)
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'create_tap_mirror',
            self.alt_target)

    def test_update_tap_mirror(self):
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'update_tap_mirror',
            self.target)
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'update_tap_mirror',
            self.alt_target)

    def test_get_tap_mirror(self):
        self.assertTrue(
            neutron_policy.enforce(self.context, 'get_tap_mirror',
            self.target))
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'get_tap_mirror',
            self.alt_target)

    def test_delete_tap_mirror(self):
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'delete_tap_mirror',
            self.target)
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'delete_tap_mirror',
            self.alt_target)


class ServiceRoleTests(TapMirrorAPITestCase):

    def setUp(self):
        super().setUp()
        self.context = self.service_ctx

    def test_create_tap_mirror(self):
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'create_tap_mirror',
            self.target)

    def test_update_tap_mirror(self):
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'update_tap_mirror',
            self.target)

    def test_get_tap_mirror(self):
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'get_tap_mirror',
            self.target)

    def test_delete_tap_mirror(self):
        self.assertRaises(
            policy.PolicyNotAuthorized,
            neutron_policy.enforce, self.context, 'delete_tap_mirror',
            self.target)
