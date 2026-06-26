# Copyright 2026 Openinfra Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import random

from neutron.tests.unit.objects import test_base as obj_test_base
from neutron.tests.unit import testlib_api
from neutron_lib.api.definitions import taas as taas_api

from neutron_taas.objects import taas as taas_objects


obj_test_base.FIELD_TYPE_VALUE_GENERATOR_MAP[
    taas_objects.TapFlowDirectionEnumField] = (
        lambda: random.choice(taas_api.DIRECTION_ENUM)
)


class TapServiceIfaceObjectTestCase(obj_test_base.BaseObjectIfaceTestCase):

    _test_class = taas_objects.TapService


class TapServiceDbObjectTestCase(obj_test_base.BaseDbObjectTestCase,
                                 testlib_api.SqlTestCase):

    _test_class = taas_objects.TapService


class TapFlowIfaceObjectTestCase(obj_test_base.BaseObjectIfaceTestCase):

    _test_class = taas_objects.TapFlow


class TapFlowDbObjectTestCase(obj_test_base.BaseDbObjectTestCase,
                              testlib_api.SqlTestCase):

    _test_class = taas_objects.TapFlow

    def setUp(self):
        super().setUp()
        self.update_obj_fields(
            {'tap_service_id': lambda: self._create_test_tap_service_id(),
             'direction': lambda: 'IN'})

    def _create_test_tap_service_id(self):
        obj = taas_objects.TapService(
            self.context,
            name='test-tap-service',
            port_id=self._create_test_port_id(),
            status='ACTIVE',
            project_id=self.db_objs[0]['project_id'],
        )
        obj.create()
        return obj.id


class _TapIdAssociationMixin:
    """Mixin to provide unique taas_id values for TapIdAssociation tests."""

    _test_class = taas_objects.TapIdAssociation
    _taas_id_counter = 0

    def get_random_object_fields(self, obj_cls=None):
        obj_cls = obj_cls or self._test_class
        if obj_cls == taas_objects.TapIdAssociation:
            _TapIdAssociationMixin._taas_id_counter += 1
            fields = {
                'taas_id': _TapIdAssociationMixin._taas_id_counter,
                'tap_service_id': None,
            }
            # Register in unique tracker to avoid recursion
            keytup = tuple(self._test_class.primary_keys)
            unique_values = tuple(
                fields[k] for k in keytup)
            self._unique_tracker[keytup].add(unique_values)
            return fields
        return super().get_random_object_fields(obj_cls)


class TapIdAssociationIfaceObjectTestCase(
        _TapIdAssociationMixin,
        obj_test_base.BaseObjectIfaceTestCase):

    _test_class = taas_objects.TapIdAssociation


class TapIdAssociationDbObjectTestCase(_TapIdAssociationMixin,
                                       obj_test_base.BaseDbObjectTestCase,
                                       testlib_api.SqlTestCase):

    _test_class = taas_objects.TapIdAssociation
