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

from neutron.conf.policies import base
from neutron_lib.policy import RULE_ADMIN_OR_OWNER


COLLECTION_PATH = '/taas/tap_flows'
RESOURCE_PATH = '/taas/tap_flows/{id}'

DEPRECATED_REASON = """
The neutron TAAS API now supports Secure RBAC default roles.
"""

rules = [
    policy.DocumentedRuleDefault(
        name='create_tap_flow',
        check_str=base.ADMIN_OR_PROJECT_MEMBER,
        scope_types=['project'],
        description='Create a tap flow',
        operations=[
            {
                'method': 'POST',
                'path': COLLECTION_PATH,
            }
        ],
        deprecated_rule=policy.DeprecatedRule(
            name='create_tap_flow',
            check_str=RULE_ADMIN_OR_OWNER,
            deprecated_reason=DEPRECATED_REASON,
            deprecated_since='2025.2')
    ),
    policy.DocumentedRuleDefault(
        name='update_tap_flow',
        check_str=base.ADMIN_OR_PROJECT_MEMBER,
        scope_types=['project'],
        description='Update a tap flow',
        operations=[
            {
                'method': 'PUT',
                'path': RESOURCE_PATH,
            }
        ],
        deprecated_rule=policy.DeprecatedRule(
            name='update_tap_flow',
            check_str=RULE_ADMIN_OR_OWNER,
            deprecated_reason=DEPRECATED_REASON,
            deprecated_since='2025.2')
    ),
    policy.DocumentedRuleDefault(
        name='get_tap_flow',
        check_str=base.ADMIN_OR_PROJECT_MEMBER,
        scope_types=['project'],
        description='Show a tap flow',
        operations=[
            {
                'method': 'GET',
                'path': RESOURCE_PATH,
            }
        ],
        deprecated_rule=policy.DeprecatedRule(
            name='get_tap_flow',
            check_str=RULE_ADMIN_OR_OWNER,
            deprecated_reason=DEPRECATED_REASON,
            deprecated_since='2025.2')
    ),
    policy.DocumentedRuleDefault(
        name='delete_tap_flow',
        check_str=base.ADMIN_OR_PROJECT_MEMBER,
        scope_types=['project'],
        description='Delete a tap flow',
        operations=[
            {
                'method': 'DELETE',
                'path': RESOURCE_PATH,
            }
        ],
        deprecated_rule=policy.DeprecatedRule(
            name='delete_tap_flow',
            check_str=RULE_ADMIN_OR_OWNER,
            deprecated_reason=DEPRECATED_REASON,
            deprecated_since='2025.2')
    ),
]


def list_rules():
    return rules
