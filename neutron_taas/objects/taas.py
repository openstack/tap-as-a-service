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

from oslo_versionedobjects import fields as obj_fields

from neutron.objects import base
from neutron_lib.api.definitions import taas as taas_api
from neutron_lib.objects import common_types

from neutron_taas.db.models import taas as taas_model


class TapFlowDirectionEnumField(obj_fields.AutoTypedField):
    AUTO_TYPE = obj_fields.Enum(taas_api.DIRECTION_ENUM)


@base.NeutronObjectRegistry.register
class TapService(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = taas_model.TapService

    fields = {
        'id': common_types.UUIDField(),
        'project_id': obj_fields.StringField(nullable=True),
        'name': obj_fields.StringField(nullable=True),
        'description': obj_fields.StringField(nullable=True),
        'port_id': common_types.UUIDField(),
        'status': obj_fields.StringField(),
    }

    fields_no_update = ['project_id', 'port_id']


@base.NeutronObjectRegistry.register
class TapFlow(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = taas_model.TapFlow

    fields = {
        'id': common_types.UUIDField(),
        'project_id': obj_fields.StringField(nullable=True),
        'name': obj_fields.StringField(nullable=True),
        'description': obj_fields.StringField(nullable=True),
        'tap_service_id': common_types.UUIDField(),
        'source_port': common_types.UUIDField(),
        'direction': TapFlowDirectionEnumField(),
        'status': obj_fields.StringField(),
        'vlan_filter': obj_fields.StringField(nullable=True),
    }

    fields_no_update = ['project_id', 'tap_service_id', 'source_port']


@base.NeutronObjectRegistry.register
class TapIdAssociation(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = taas_model.TapIdAssociation

    primary_keys = ['taas_id']

    fields = {
        'taas_id': obj_fields.IntegerField(),
        'tap_service_id': common_types.UUIDField(nullable=True),
    }
