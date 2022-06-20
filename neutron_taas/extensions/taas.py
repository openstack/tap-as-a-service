# Copyright (C) 2015 Ericsson AB
# Copyright (c) 2015 Gigamon
#
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

import abc

from neutron_lib.api.definitions import taas as taas_api_def
from neutron_lib.api import extensions
from neutron_lib.services import base as service_base

from neutron.api.v2 import resource_helper

from neutron_taas.common import config


config.register()


class Taas(extensions.APIExtensionDescriptor):

    api_definition = taas_api_def

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plural_mappings = resource_helper.build_plural_mappings(
            {}, taas_api_def.RESOURCE_ATTRIBUTE_MAP)

        resources = resource_helper.build_resource_info(
            plural_mappings,
            taas_api_def.RESOURCE_ATTRIBUTE_MAP,
            taas_api_def.ALIAS,
            translate_name=False,
            allow_bulk=True)

        return resources

    @classmethod
    def get_plugin_interface(cls):
        return TaasPluginBase


class TaasPluginBase(service_base.ServicePluginBase, metaclass=abc.ABCMeta):

    def get_plugin_description(self):
        return taas_api_def.DESCRIPTION

    @classmethod
    def get_plugin_type(cls):
        return taas_api_def.ALIAS

    @abc.abstractmethod
    def create_tap_service(self, context, tap_service):
        """Create a Tap Service."""
        pass

    @abc.abstractmethod
    def delete_tap_service(self, context, id):
        """Delete a Tap Service."""
        pass

    @abc.abstractmethod
    def get_tap_service(self, context, id, fields=None):
        """Get a Tap Service."""
        pass

    @abc.abstractmethod
    def get_tap_services(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        """List all Tap Services."""
        pass

    @abc.abstractmethod
    def update_tap_service(self, context, id, tap_service):
        """Update a Tap Service."""
        pass

    @abc.abstractmethod
    def create_tap_flow(self, context, tap_flow):
        """Create a Tap Flow."""
        pass

    @abc.abstractmethod
    def get_tap_flow(self, context, id, fields=None):
        """Get a Tap Flow."""
        pass

    @abc.abstractmethod
    def delete_tap_flow(self, context, id):
        """Delete a Tap Flow."""
        pass

    @abc.abstractmethod
    def get_tap_flows(self, context, filters=None, fields=None,
                      sorts=None, limit=None, marker=None,
                      page_reverse=False):
        """List all Tap Flows."""
        pass

    @abc.abstractmethod
    def update_tap_flow(self, context, id, tap_flow):
        """Update a Tap Flow."""
        pass
