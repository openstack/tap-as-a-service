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

import abc

from neutron_lib.api.definitions import tap_mirror as tap_mirror_api_def
from neutron_lib.api import extensions as api_extensions
from neutron_lib.services import base as service_base

from neutron.api.v2 import resource_helper


class Tap_mirror(api_extensions.APIExtensionDescriptor):

    api_definition = tap_mirror_api_def

    @classmethod
    def get_resources(cls):
        plural_mappings = resource_helper.build_plural_mappings(
            {}, tap_mirror_api_def.RESOURCE_ATTRIBUTE_MAP)
        resources = resource_helper.build_resource_info(
            plural_mappings,
            tap_mirror_api_def.RESOURCE_ATTRIBUTE_MAP,
            tap_mirror_api_def.ALIAS,
            translate_name=False,
            allow_bulk=False)

        return resources

    @classmethod
    def get_plugin_interface(cls):
        return TapMirrorBase


class TapMirrorBase(service_base.ServicePluginBase, metaclass=abc.ABCMeta):

    def get_plugin_description(self):
        return tap_mirror_api_def.DESCRIPTION

    @classmethod
    def get_plugin_type(cls):
        return tap_mirror_api_def.ALIAS

    @abc.abstractmethod
    def create_tap_mirror(self, context, tap_mirror):
        """Create a Tap Mirror."""
        pass

    @abc.abstractmethod
    def get_tap_mirror(self, context, id, fields=None):
        """Get a Tap Mirror."""
        pass

    @abc.abstractmethod
    def get_tap_mirrors(self, context, filters=None, fields=None,
                        sorts=None, limit=None, marker=None,
                        page_reverse=False):
        """List all Tap Mirrors."""
        pass

    @abc.abstractmethod
    def delete_tap_mirror(self, context, id):
        """Delete a Tap Mirror."""
        pass

    @abc.abstractmethod
    def update_tap_mirror(self, context, id, tap_mirror):
        """Update a Tap Mirror."""
        pass
