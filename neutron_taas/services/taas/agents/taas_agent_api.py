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

from neutron_lib import rpc as n_rpc
import oslo_messaging as messaging


class TaasPluginApiMixin:

    # Currently there are no Calls the Agent makes towards the Plugin.

    def __init__(self, topic, host):
        self.host = host
        target = messaging.Target(topic=topic, version='1.0')
        self.client = n_rpc.get_client(target)
        super().__init__()


class TaasAgentRpcCallbackMixin:
    """Mixin for Taas agent Implementations."""

    def __init__(self):
        super().__init__()

    def consume_api(self, agent_api):
        """Receive neutron agent API object

        Allows an extension to gain access to resources internal to the
        neutron agent and otherwise unavailable to the extension.
        """
        self.agent_api = agent_api

    def create_tap_service(self, context, tap_service_msg, host):
        """Handle RPC cast from plugin to create a tap service."""
        pass

    def delete_tap_service(self, context, tap_service_msg, host):
        """Handle RPC cast from plugin to delete a tap service."""
        pass

    def create_tap_flow(self, context, tap_flow_msg, host):
        """Handle RPC cast from plugin to create a tap flow"""
        pass

    def delete_tap_flow(self, context, tap_flow_msg, host):
        """Handle RPC cast from plugin to delete a tap flow"""
        pass

    def create_tap_mirror(self, context, tap_mirror_msg, host):
        """Handle RPC cast from plugin to create a Tap Mirror."""
        pass

    def delete_tap_mirror(self, context, tap_mirror_msg, host):
        """Handle RPC cast from plugin to delete a Tap Mirror."""
        pass
