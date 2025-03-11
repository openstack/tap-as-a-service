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

import neutron.services.provider_configuration

import neutron_taas.common.config
import neutron_taas.services.taas.agents.extensions.taas


def list_agent_opts():
    return [
        ('DEFAULT', neutron_taas.services.taas.agents.extensions.taas.OPTS)
    ]


def list_opts():
    return [
        ('service_providers',
         neutron.services.provider_configuration.serviceprovider_opts),
        ('quotas', neutron_taas.common.config.taas_quota_opts),
        ('taas', neutron_taas.common.config.taas_opts)
    ]
