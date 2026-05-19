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

from unittest import mock

from neutron_taas.services.taas.agents.common import taas_agent
from neutron_taas.tests import base


class TestTaasAgentRpcCallbackPeriodicTasks(base.TaasTestCase):
    def setUp(self):
        super().setUp()
        self.callback = taas_agent.TaasAgentRpcCallback.__new__(
            taas_agent.TaasAgentRpcCallback)
        self.callback.taas_driver = mock.Mock()
        self.callback.taas_plugin_rpc = mock.Mock()
        self.callback.conf = mock.Mock()
        self.callback.func_dict = {
            'periodic_tasks': {'msg_name': 'periodic_tasks'}
        }

    def test_periodic_tasks_accepts_context(self):
        """periodic_tasks must accept a context arg.

        This matches the Neutron L2 extension manager callback.
        """
        ctx = mock.Mock()
        with mock.patch.object(self.callback,
                               '_invoke_driver_for_plugin_api') as m:
            self.callback.periodic_tasks(context=ctx)
            m.assert_called_once_with(
                context=ctx,
                args=[],
                func_name='periodic_tasks')

    def test_periodic_tasks_default_context_none(self):
        """periodic_tasks must work with no args.

        This matches the timer-based invocation path.
        """
        with mock.patch.object(self.callback,
                               '_invoke_driver_for_plugin_api') as m:
            self.callback.periodic_tasks()
            m.assert_called_once_with(
                context=None,
                args=[],
                func_name='periodic_tasks')
