
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#


import copy
from neutron_lib.api.definitions import taas
from neutron_lib.api.definitions import tap_mirror
from neutron_lib.api import extensions as api_extensions

ALIAS = 'tap-mirror-both-direction'
IS_SHIM_EXTENSION = False
IS_STANDARD_ATTR_EXTENSION = False
NAME = "Tap as a Service mirror with BOTH direction support"
DESCRIPTION = ("Neutron Tap as a Service extension mirroring with support "
               "for BOTH direction.")
UPDATED_TIMESTAMP = "2025-12-15T11:45:00-00:00"
DIRECTION_SPEC = copy.deepcopy(tap_mirror.DIRECTION_SPEC)
DIRECTION_SPEC['type:dict'][taas.DIRECTION_BOTH] = {
    'type:integer': None, 'default': None, 'required': False
}
RESOURCE_ATTRIBUTE_MAP = {
    tap_mirror.COLLECTION_NAME: {
        'directions': {
            'allow_post': True, 'allow_put': False,
            'validate': DIRECTION_SPEC,
            'is_visible': True},
    }
}
SUB_RESOURCE_ATTRIBUTE_MAP = None
ACTION_MAP = {}
ACTION_STATUS = {}
REQUIRED_EXTENSIONS = [tap_mirror.ALIAS]
OPTIONAL_EXTENSIONS = []

# TODO(egarciar): use api definition from neutron-lib once
# https://review.opendev.org/c/openstack/neutron-lib/+/969962
# is merged and released


class Tap_mirror_both_direction(api_extensions.ExtensionDescriptor):
    """Extension class supporting tap mirror both direction."""

    @classmethod
    def get_name(cls):
        return NAME

    @classmethod
    def get_alias(cls):
        return ALIAS

    @classmethod
    def get_description(cls):
        return DESCRIPTION

    @classmethod
    def get_updated(cls):
        return UPDATED_TIMESTAMP

    def get_required_extensions(self):
        return REQUIRED_EXTENSIONS

    def get_extended_resources(self, version):
        return RESOURCE_ATTRIBUTE_MAP
