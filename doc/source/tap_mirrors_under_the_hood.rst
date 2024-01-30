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


Open vSwitch tap mirror driver
==============================

Since OVS v2.10 it is possible to create GRE or ERSPAN mirroring ports.

.. code-block:: console

 $ ovs-vsctl add-port br0 at_erspan0 -- set int at_erspan0 type=erspan options:key=1 options:remote_ip=172.31.1.1 options:erspan_ver=1 options:erspan_idx=1
 $ # type can be erspan or gre, and
 $ # options:erspan_ver=1 or 2 selects the version of ERSPAN.
 $ # Note that tap mirroring uses erspan_ver=1

To create a tap mirror with the OVS driver you have to enable ``TaasRpcDriver`` in the
``taas_plugin.ini`` configuration file:

.. code-block:: ini

    [service_providers]
    service_provider = TAAS:TAAS:neutron_taas.services.taas.service_drivers.taas_rpc.TaasRpcDriver:default

.. note::

    The same driver must be set to use taas with tap-services and tap-flows.

The Openstack CLI workflow is the following to create an ERSPANv1 mirror:

.. code-block:: bash

 $ openstack network create net0
 $ openstack subnet create subnet0 --subnet-range <CIDR of the subnet> --network net0
 $ openstack port create mirror_port --network net0
 $ openstack server create --flavor <flavor ID> --image <Image name or ID> --nic port-id=mirror_port  mirror_vm0
 $ openstack tap mirror create --port mirror_port --name mirror1 --directions IN=102 --remote-ip 100.109.0.221 --mirror-type erspanv1
 +-------------+--------------------------------------+
 | Field       | Value                                |
 +-------------+--------------------------------------+
 | description |                                      |
 | directions  | {'IN': '102'}                        |
 | id          | 7171328e-fcfe-40ab-8e27-84ce7d57a5cd |
 | mirror_type | erspanv1                             |
 | name        | mirror1                              |
 | port_id     | 88316ec8-38ca-4115-912a-3d7fab2d6cf7 |
 | project_id  | fe7c0b79c37b439490d2274405ebf483     |
 | remote_ip   | 100.109.0.221                        |
 +-------------+--------------------------------------+

The result of the above commands will result in a new port on ``br-tap``:

.. code-block:: bash

  $ sudo ovs-vsctl show
  ...
     Bridge br-tap
        datapath_type: system
        Port br-tap
            Interface br-tap
                type: internal
        Port tm_in_c00403
            Interface tm_in_c00403
                type: erspan
                options: {erspan_idx="102", erspan_ver="1", key="102", remote_ip="100.109.0.221"}
        Port patch-tap-int
            Interface patch-tap-int
                type: patch
                options: {peer=patch-int-tap}
        Port patch-tap-tun
            Interface patch-tap-tun
                type: patch
                options: {peer=patch-tun-tap}

On ``br-int`` new flows are installed to direct the traffic (in this case only ingress) towards ``br-tap``:

.. code-block:: bash

  $ sudo ovs-ofctl dump-flows br-int
   ...
   cookie=0x8f7b2f67055cd027, duration=1282.245s, table=0, n_packets=0, n_bytes=0, idle_age=1282, priority=20,dl_dst=<mac of the mirror_port> actions=output:4,resubmit(,58)

.. note::

   output:4 points to patch-tap-int.

The resulting packet will be like this:

.. code-block:: bash

 Frame 1: 148 bytes on wire (1184 bits), 148 bytes captured (1184 bits)
 Ethernet II, Src: RealtekU_16:01:cb (52:54:00:16:01:cb), Dst: RealtekU_8e:0e:4b (52:54:00:8e:0e:4b)
 Internet Protocol Version 4, Src: 100.109.0.82, Dst: 100.109.0.221
 Generic Routing Encapsulation (ERSPAN)
 Encapsulated Remote Switch Packet ANalysis Type II
     0001 .... .... .... = Version: Type II (1)
     .... 0000 0000 0000 = Vlan: 0
     000. .... .... .... = COS: 0
     ...0 0... .... .... = Encap: Originally without VLAN tag (0)
     .... .0.. .... .... = Truncated: Not truncated (0)
     .... ..00 0110 0110 = SpanID: 102
     0000 0000 0000 .... .... .... .... .... = Reserved: 0
     .... .... .... 0000 0000 0001 0000 0010 = Index: 258
 Ethernet II, Src: fa:16:3e:4c:0c:be (fa:16:3e:4c:0c:be), Dst: fa:16:3e:1d:e4:f4 (fa:16:3e:1d:e4:f4)
 Internet Protocol Version 4, Src: 192.171.0.23, Dst: 192.171.0.6
 Internet Control Message Protocol

``SpanID`` is ``102`` as expected but the ``Index`` is ``258`` which is ``0x102``

OVN tap mirror driver
=====================

Since OVN v22.12.0 it is possible to create mirrors:

.. code-block:: console

 $ ovn-nbctl mirror-add mirror1 erspan 0 from-lport 100.109.0.48
 $ # type (2nd parameter after name) can be erspan or gre or local (from a later version)
 $ # index (3rd parameter) is the tunnel id and the base of ERSPAN idx
 $ # filter (4th parameter) can be from-lport, to-lport or both (from a later version)
 $ # sink (5th parameter) is the remote IP of the mirroring.

To create a tap mirror with the OVN driver you have to enable ``TaasOvnDriver`` in the
``taas_plugin.ini`` configuration file:

.. code-block:: ini

    [service_providers]
    service_provider = TAAS:TAAS:neutron_taas.services.taas.service_drivers.ovn.taas_ovn.TaasOvnDriver:default

The Openstack CLI workflow is the following to create an ERSPANv1 mirror:

.. code-block:: bash

 $ openstack network create net0
 $ openstack subnet create subnet0 --subnet-range <CIDR of the subnet> --network net0
 $ openstack port create mirror_port --network net0
 $ openstack server create --flavor <flavor ID> --image <Image name or ID> --nic port-id=mirror_port  mirror_vm0
 $ openstack tap mirror create --port mirror_port --name mirror1 --directions IN=102 --remote-ip 100.109.0.221 --mirror-type erspanv1
 +-------------+--------------------------------------+
 | Field       | Value                                |
 +-------------+--------------------------------------+
 | description |                                      |
 | directions  | {'IN': '102'}                        |
 | id          | 7171328e-fcfe-40ab-8e27-84ce7d57a5cd |
 | mirror_type | erspanv1                             |
 | name        | mirror1                              |
 | port_id     | 88316ec8-38ca-4115-912a-3d7fab2d6cf7 |
 | project_id  | fe7c0b79c37b439490d2274405ebf483     |
 | remote_ip   | 100.109.0.221                        |
 +-------------+--------------------------------------+

The result of the above commands will result a new mirror in the ovn nbdb:

.. code-block:: bash

 $ ovn-nbctl mirror-list
 tm_in_717132:
  Type     :  erspan
  Sink     :  100.109.0.221
  Filter   :  to-lport
  Index/Key:  102

Note the "translation" of the parameters.
Directions IN=102 will Filter=to-lport, and Index/Key:102.
(OUT direction of course will be from-lport in OVN NBDB)

And of course the port will appear on the integration bridge also:

.. code-block:: bash

 $ ovs-vsctl show
 ...
     Bridge br-int
         ....
         Port ovn-tm_in_717132
             Interface ovn-tm_in_717132
                 type: erspan
                 options: {erspan_idx="102", erspan_ver="1", key="102", remote_ip="100.109.0.221"}

Please note the ERSPAN header fields also:

.. code-block:: bash

 Frame 1: 148 bytes on wire (1184 bits), 148 bytes captured (1184 bits)
 Ethernet II, Src: RealtekU_3d:93:57 (52:54:00:3d:93:57), Dst: RealtekU_8e:0e:4b (52:54:00:8e:0e:4b)
 Internet Protocol Version 4, Src: 100.109.0.48, Dst: 100.109.0.221
 Generic Routing Encapsulation (ERSPAN)
 Encapsulated Remote Switch Packet ANalysis Type II
     0001 .... .... .... = Version: Type II (1)
     .... 0000 0000 0000 = Vlan: 0
     000. .... .... .... = COS: 0
     ...0 0... .... .... = Encap: Originally without VLAN tag (0)
     .... .0.. .... .... = Truncated: Not truncated (0)
     .... ..00 0110 0110 = SpanID: 102
     0000 0000 0000 .... .... .... .... .... = Reserved: 0
     .... .... .... 0000 0000 0001 0000 0010 = Index: 258
 Ethernet II, Src: fa:16:3e:50:ed:fd (fa:16:3e:50:ed:fd), Dst: fa:16:3e:6a:49:13 (fa:16:3e:6a:49:13)
 Internet Protocol Version 4, Src: 192.171.0.25, Dst: 192.171.0.27
 Internet Control Message Protocol

``SpanID`` is ``102`` as expected but the ``Index`` is ``258`` which is ``0x102``
