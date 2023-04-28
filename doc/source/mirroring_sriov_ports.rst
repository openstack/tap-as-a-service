..
      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.


      Convention for heading levels in Neutron devref:
      =======  Heading 0 (reserved for the title in a document)
      -------  Heading 1
      ~~~~~~~  Heading 2
      +++++++  Heading 3
      '''''''  Heading 4
      (Avoid deeper levels because they do not render well.)


SriovNic taas driver
====================

The SRIOV mirroring for tap-as-a-service was proposed in Stein cycle, in
`Port Mirroring API for VF Mirroring <https://specs.openstack.org/openstack/neutron-specs/specs/stein/port-mirroring-sriov-vfs.html>`_.

The proposal was to use the ``Intel Ethernet Network Adapter XXV710``
capabilities with at least ``Intel i40e v4.16.0`` driver for mirroring traffic
on VFs.

Configuration
-------------

To enable the OVS taas driver you need these config options in ``ml2_conf.ini`` on
all hosts where ovs-neutron-agent is running::

    [agent]
    extensions = taas

You also need a ``taas_plugin.ini`` with the necessary service_provider setting::

    [service_providers]
    service_provider = TAAS:TAAS:neutron_taas.services.taas.service_drivers.taas_rpc.TaasRpcDriver:default

Driver
------

The driver works in a way that the traffic on the port of the ``tap-flow``,
the source of the mirroring is mirrored to the port of the ``tap-service``.
Both the tap-flow port and the tap-service port must be on the same host
and on the same Physical Function (PF).

The actual mirroring with the SRIOV driver is done by ``sysfs`` commands,
for example (from `Port Mirroring API for VF Mirroring of specific VLANs to VF <https://specs.openstack.org/openstack/neutron-specs/specs/stein/port-mirroring-sriov-vfs.html#id5>`_)::

    # # Mirror VLANs 2,18-22 of VF3 to p1p1
    # echo add 2,18-22>/sys/class/net/p1p1/device/sriov/3/vlan_mirror

    # # Remove VLAN mirroring of VLANs 2,18 of VF3 from p1p1
    # echo rem 2,18>/sys/class/net/p1p1/device/sriov/3/vlan_mirror

The driver allows the selection of specific VLANs for mirroring, and taas API
was also adopted to it, with the extra ``vlan_filter`` field for tap-flows,
see the `API ref <?expanded=create-port-detail,bulk-create-ports-detail,create-tap-flow-detail#ports>`_.

To achieve the above mirroring the following CLI command can be used::

    $ openstack tap service create --name tap_service --port port_ts
    $ openstack tap flow create --name tap_flow0 --port port0 --vlan-filter 2,18-22 --tap-service tap_service
