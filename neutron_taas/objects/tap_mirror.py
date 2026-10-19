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

import netaddr

from oslo_serialization import jsonutils
from oslo_versionedobjects import fields as obj_fields

from neutron.objects import base
from neutron_lib.objects import common_types

from neutron_taas.db.models import tap_mirror as tap_m_model


@base.NeutronObjectRegistry.register
class TapMirror(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = tap_m_model.TapMirror

    fields = {
        'id': common_types.UUIDField(),
        'project_id': obj_fields.StringField(nullable=True),
        'name': obj_fields.StringField(nullable=True),
        'description': obj_fields.StringField(nullable=True),
        'port_id': common_types.UUIDField(),
        'directions': obj_fields.DictOfStringsField(),
        'remote_ip': obj_fields.IPAddressField(),
        'mirror_type': obj_fields.StringField(),
    }

    fields_no_update = ['project_id', 'port_id', 'directions', 'remote_ip',
                        'mirror_type']

    @classmethod
    def modify_fields_from_db(cls, db_obj):
        result = super().modify_fields_from_db(db_obj)
        if 'directions' in result:
            result['directions'] = jsonutils.loads(result['directions'])
        if 'remote_ip' in result and result['remote_ip'] is not None:
            result['remote_ip'] = netaddr.IPAddress(result['remote_ip'])
        return result

    @classmethod
    def modify_fields_to_db(cls, fields):
        result = super().modify_fields_to_db(fields)
        if 'directions' in result:
            if isinstance(result['directions'], list):
                result['directions'] = [
                    jsonutils.dumps(d) for d in result['directions']]
            else:
                result['directions'] = jsonutils.dumps(result['directions'])
        if 'remote_ip' in result and result['remote_ip'] is not None:
            if isinstance(result['remote_ip'], list):
                result['remote_ip'] = [str(ip) for ip in result['remote_ip']]
            else:
                result['remote_ip'] = str(result['remote_ip'])
        return result
