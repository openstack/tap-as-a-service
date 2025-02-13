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


COLLECTION_PATH = '/taas/tap_mirrors'
RESOURCE_PATH = '/taas/tap_mirrors/{id}'

rules = [
    policy.DocumentedRuleDefault(
        name='create_tap_mirror',
        check_str=base.ADMIN_OR_PROJECT_MEMBER,
        scope_types=['project'],
        description='Create a Tap Mirror',
        operations=[
            {
                'method': 'POST',
                'path': COLLECTION_PATH
            }
        ],
    ),
    policy.DocumentedRuleDefault(
        name='update_tap_mirror',
        check_str=base.ADMIN_OR_PROJECT_MEMBER,
        scope_types=['project'],
        description='Update a Tap Mirror',
        operations=[
            {
                'method': 'PUT',
                'path': RESOURCE_PATH
            }
        ],
    ),
    policy.DocumentedRuleDefault(
        name='get_tap_mirror',
        check_str=base.ADMIN_OR_PROJECT_READER,
        scope_types=['project'],
        description='Show a Tap Mirror',
        operations=[
            {
                'method': 'GET',
                'path': COLLECTION_PATH
            },
            {
                'method': 'GET',
                'path': RESOURCE_PATH
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        name='delete_tap_mirror',
        check_str=base.ADMIN_OR_PROJECT_MEMBER,
        scope_types=['project'],
        description='Delete a Tap Mirror',
        operations=[
            {
                'method': 'DELETE',
                'path': RESOURCE_PATH,
            }
        ]
    ),
]


def list_rules():
    return rules
