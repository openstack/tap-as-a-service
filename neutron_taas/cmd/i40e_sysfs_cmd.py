
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

import argparse
import os
import pathlib
import subprocess  # nosec: B404


def main():
    parser = argparse.ArgumentParser(
        prog='i40e_sysfs_command',
        usage='1. VLANs to VF mirroring: %(prog)s <phy_device_name>'
              '<dest_vf_index> <vlan_mirror> <add|rem> <vlan_ranges_string>'
              '2. VF to VF mirroring: %(prog)s <phy_device_name>'
              '<src_vf_index> <ingress_mirror|egress_mirror> <add|rem> '
              '<dest_vf_index>'
    )
    parser.add_argument('phy_device_name')
    parser.add_argument('vf_index',
                        help='In case of VLANs to VF mirroring this is '
                        'dest_vf_index, in case of VF to VF mirroring this '
                        'is src_vf_index')
    parser.add_argument('mirror',
                        help='In case of VLANs to VF mirroring this is '
                        'vlan_mirror, in case of VF to VF mirroring this '
                        'is ingress_mirror or egress_mirror')
    parser.add_argument('add_rem', help="This can be the string add or rem")
    parser.add_argument('vlan_range_or_dest_vf',
                        help='In case of VLANs to VF mirroring this is '
                        'vlan_ranges_string, in case of VF to VF mirroring'
                        'this is dest_vf_index')
    args = parser.parse_args()

    my_device = pathlib.Path("/sys/class/net/%s/device/sriov/%s/%s" % (
        args.phy_device_name, args.vf_index, args.mirror
    ))
    if my_device.is_file():
        subprocess.run(
            ['/usr/bin/echo', args.add_rem, args.vlan_range_or_dest_vf,
             '>', '/sys/class/net/%s/device/sriov/%s/%s' % (
                 args.phy_device_name, args.vf_index,
                 args.mirror)], check=True, shell=False)  # nosec B603
    else:
        print("Invalid sysfs path: /sys/class/net/%s/device/sriov/%s/%s" %
              (args.phy_device_name, args.vf_index, args.mirror))
        os._exit(1)


if __name__ == '__main__':
    main()
