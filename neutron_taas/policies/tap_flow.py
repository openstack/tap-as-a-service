#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from oslo_policy import policy

from neutron_lib.policy import RULE_ADMIN_OR_OWNER

rules = [
    policy.DocumentedRuleDefault(
        'create_tap_flow',
        RULE_ADMIN_OR_OWNER,
        'Create a tap flow',
        [
            {
                'method': 'POST',
                'path': '/taas/tap_flows',
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        'update_tap_flow',
        RULE_ADMIN_OR_OWNER,
        'Update a tap flow',
        [
            {
                'method': 'PUT',
                'path': '/taas/tap_flows/{id}',
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_tap_flow',
        RULE_ADMIN_OR_OWNER,
        'Show a tap flow',
        [
            {
                'method': 'GET',
                'path': '/taas/tap_flows/{id}',
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        'delete_tap_flow',
        RULE_ADMIN_OR_OWNER,
        'Delete a tap flow',
        [
            {
                'method': 'DELETE',
                'path': '/taas/tap_flows/{id}',
            }
        ]
    ),
]


def list_rules():
    return rules
