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
        'create_tap_service',
        RULE_ADMIN_OR_OWNER,
        'Create a tap service',
        [
            {
                'method': 'POST',
                'path': '/taas/tap_services',
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        'update_tap_service',
        RULE_ADMIN_OR_OWNER,
        'Updates a tap service',
        [
            {
                'method': 'PUT',
                'path': '/taas/tap_services/{id}',
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_tap_service',
        RULE_ADMIN_OR_OWNER,
        'Show a tap service',
        [
            {
                'method': 'GET',
                'path': '/taas/tap_services/{id}',
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        'delete_tap_service',
        RULE_ADMIN_OR_OWNER,
        'Delete a tap service',
        [
            {
                'method': 'DELETE',
                'path': '/taas/tap_services/{id}',
            }
        ]
    ),
]


def list_rules():
    return rules
