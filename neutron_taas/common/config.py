# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from oslo_config import cfg

from neutron_taas._i18n import _


taas_quota_opts = [
    cfg.IntOpt('quota_tap_service',
               default=1,
               help=_('Number of Tap Service instances allowed per tenant')),
    cfg.IntOpt('quota_tap_flow',
               default=10,
               help=_('Number of Tap flows allowed per tenant'))
]


TaasOpts = [
    cfg.IntOpt(
        'vlan_range_start',
        default=3900,
        help=_("Starting range of TAAS VLAN IDs")),
    cfg.IntOpt(
        'vlan_range_end',
        default=4000,
        help=_("End range of TAAS VLAN IDs")),
]


def register():
    cfg.CONF.register_opts(taas_quota_opts, 'QUOTAS')
    cfg.CONF.register_opts(TaasOpts, 'taas')
