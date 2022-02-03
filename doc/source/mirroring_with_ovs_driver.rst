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


Open vSwitch taas driver
========================

The OVS driver for taas uses the existing infrastructure created by Neutron:
br-int, br-tun, and adds an extra bridge br-tap for mirroring.

For ``ingress``/``egress`` terminology please check out:
`Open vSwitch Firewall Driver Ingress/Egress Terminology
<https://docs.openstack.org/neutron/latest/contributor/internals/openvswitch_firewall.html#ingress-egress-terminology>`_.

Configuration
-------------

To enable the OVS taas driver you need these config options in ``ml2_conf.ini`` on
all hosts where ovs-neutron-agent is running::

    [agent]
    extensions = taas

You also need a ``taas_plugin.ini`` with the necessary service_provider setting::

    [service_providers]
    service_provider = TAAS:TAAS:neutron_taas.services.taas.service_drivers.taas_rpc.TaasRpcDriver:default

Openflow rules
--------------

Topology
~~~~~~~~

TAAS (``OvsTaasDriver`` class) creates ``br-tap`` when the driver is starting,
then created patch ports to connect it with br-int and br-tun.

::

    +----------+                  +---------+                     +--------+
    |          |(patch-int-tap)   |         |(patch-tap-tun)      |        |
    | br-int   |------------------| br-tap  |---------------------| br-tun |
    |          |   (patch-tap-int)|         |      (patch-tun-tap)|        |
    +----------+                  +---------+                     +--------+


Installed flows on br-int
~~~~~~~~~~~~~~~~~~~~~~~~~

Create tap service
++++++++++++++++++

Add flow to table 0 to match packets coming from ``patch_int_tap`` to mod_vlan
to the original port (associated to tap service) VLAN, and output on the port.

Create tap flow
+++++++++++++++

If the direction of the tap flow is ``OUT`` or ``BOTH`` match packets coming
from the port associated with the tap flow, mod_vlan to the tap service VLAN
(taas_id in the code) and output to ``patch_int_tap``.

If direction is ``IN`` or ``BOTH`` match flows with the mac of the port
associated with the tap flow, mod_vlan to the tap service VLAN
(taas_id in the code) and output to ``patch_int_tap``.

Installed flows on br-tun
~~~~~~~~~~~~~~~~~~~~~~~~~

The tables used on br-tun are in [1]_

OvsTaasDriver during initialization uses table 0 to filter out packets coming
from ``patch_tun_tap`` and resubmit them to ``TAAS_SEND_UCAST``, and to
``TAAS_SEND_FLOOD``.
In table ``TAAS_SEND_FLOOD`` flood flow actions are installed for all ports
except ``patch-int`` and ``patch-tun-tap``.
Table ``TAAS_CLASSIFY`` is used to filter packets based on ``reg0`` value
(which is set during tap service or tap flow creation, to have the same rules
on both the tap service and tap flow hosts):

* reg0=0 or 1 resubmit to ``TAAS_DST_CHECK``
* reg0=2 resubmit to ``TAAS_SRC_CHECK``

In table ``TAAS_DST_RESPOND`` flow filters for ``reg0=1``, VLAN is modified
to 2, and VLAN_TCI least significant bits moved to TUN_ID, and packet is sent
out in in_port. Flow to send packets to table ``TAAS_DST_RESPOND`` is
installed during tap service creation.

In table ``TAAS_SRC_RESPOND`` a learn action is installed.

Create tap service
++++++++++++++++++

For every tunnel type (GRE, VXLAN, GENEVE) a flow is installed to match
packets whose ``tun_id`` equals to the tap service VLAN (taas_id in the code)
and resubmit to ``TAAS_CLASSIFY``. This is the flow that moves VLAN_TCI least
significant 11 bits to ``REG0``, that is the VID.

To table ``TAAS_DST_CHECK`` a flow is installed to match flows which tun_id
equals with the tap service VLAN (taas_id in the code) and resubmit to
``TAAS_DST_RESPOND``.

Create tap flow
+++++++++++++++

For every tunnel type (GRE, VXLAN, GENEVE) a flow is installed to match
packets whose ``tun_id`` equals to the tap service VLAN (taas_id in the code)
and resubmit to ``TAAS_CLASSIFY``. This is the flow that moves VLAN_TCI least
significant 11 bits to ``REG0``, that is the VID.

To table ``TAAS_SRC_CHECK`` a flow is installed to match flows which tun_id
equals with the tap service VLAN (taas_id in the code) and resubmit to
``TAAS_SRC_RESPOND``.

Installed flows on br-tap
~~~~~~~~~~~~~~~~~~~~~~~~~

The tables used on br-tap are in [2]_.

OvsTaasDriver uses table 0 to filter out packets coming from ``patch_tap_int``
and resubmit them to table ``TAAS_RECV_LOC``, and from there send out on
patch_tap_tun.
On the other direction if packets in table 0 are coming from ``patch_tap_tun``
then those are resubmitted to ``TAAS_RECV_REM``.

Create tap service
++++++++++++++++++

When tap service is created the OVS TaaS driver filters out packets in
``TAAS_RECV_LOC`` with the VLAN dedicated to the tap service from the
``vlan_range`` (see [3]_) and sends them back.

On the other direction if packets coming from table ``TAAS_RECV_REM`` and
they have the tap service VLAN (taas_id in the driver code) output them
to ``patch_tap_int`` towards br-int.

Flow rules example
------------------

::

  +---------+                                 +----------+
  |         |                                 | Monitor  |
  | VM0     |                                 |   VM     |
  |         |                                 |          |
  +---------+                                 +----------+
     |  |Port0 (associated to tap flow)           |  |Port_ts (associated to
     +--+ -----------                             +--+   tap service)
      |      net0    \               monitor_net    |  -------+
   ---+------------   |                       ------+--------  \
                      |                                        /
            +---------+-+                          +---------+
           /             \                        /           \
           | tap_flow0    | -------------------- | tap_service |
           \              /                       \            /
            +------------+                         +----------+

Flows after the driver is started
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``br-tun``

::

  table=0,   priority=1,in_port="patch-tun-tap"  actions=resubmit(,30)
  table=30,  priority=0                          actions=resubmit(,31)
  table=31,  hard_age=1,                         actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID[0..11],mod_vlan_vid:1,output:"vxlan-646d00d9"
  table=35,  priority=1,reg0=0x1                 actions=resubmit(,36)
  table=35,  priority=1,reg0=0x2                 actions=resubmit(,37)
  table=35,  priority=2,reg0=0                   actions=resubmit(,36)
  table=36,  priority=0                          actions=drop
  table=37,  priority=0                          actions=drop
  table=38,  priority=1,reg0=0x1                 actions=output:"patch-tun-tap",move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID[0..11],mod_vlan_vid:2,IN_PORT
  table=38,  priority=2,reg0=0                   actions=output:"patch-tun-tap"
  table=39,  priority=1                          actions=learn(table=30,hard_timeout=60,priority=1,NXM_OF_VLAN_TCI[0..11],load:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID[0..11],load:0->NXM_OF_VLAN_TCI[0..11],output:NXM_OF_IN_PORT[])

* table 30: TAAS_SEND_UCAST
* table 31: TAAS_SEND_FLOOD
* table 35: TAAS_CLASSIFY
* table 36: TAAS_DST_CHECK
* table 37: TAAS_SRC_CHECK
* table 38: TAAS_DST_RESPOND
* table 39: TAAS_SRC_RESPOND
* vxlan-646d00d9: vxlan port on the host

``br-tap``

::

  table=0,  priority=0                         actions=drop
  table=0,  priority=1,in_port="patch-tap-int" actions=resubmit(,1)
  table=0,  priority=1,in_port="patch-tap-tun" actions=resubmit(,2)
  table=1,  priority=0                         actions=output:"patch-tap-tun"
  table=2,  priority=0                         actions=drop


* table 1: TAAS_RECV_LOC
* table 2: TAAS_RECV_REM

Create tap service
~~~~~~~~~~~~~~~~~~

The used command:

.. code-block:: console

  $ openstack tap service create --name tap_service --port port_ts

``br-int``

::

  table=0,   priority=25,in_port="patch-int-tap",dl_vlan=3900   actions=mod_vlan_vid:5,output:"tap12df65fe-ce"

* VLAN 3900: taas id (vlan_range_start default value)
* tap12df65fe-ce:  tap port id in br-int for the port associated with the tap service

``br-tun``

::

  table=3,   priority=1,tun_id=0xf3c   actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID[0..11]->NXM_OF_VLAN_TCI[0..11],resubmit(,35)
  table=4,   priority=1,tun_id=0xf3c   actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID[0..11]->NXM_OF_VLAN_TCI[0..11],resubmit(,35)
  table=6,   priority=1,tun_id=0xf3c   actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID[0..11]->NXM_OF_VLAN_TCI[0..11],resubmit(,35)
  table=36,  priority=1,tun_id=0xf3c   actions=resubmit(,38)

* table 3: GRE_TUN_TO_LV
* table 4: VXLAN_TUN_TO_LV
* table 6: GENEVE_TUN_TO_LV
* table 36: TAAS_DST_CHECK
* table 38: TAAS_DST_RESPOND
* tun_id=0xf3c => VLAN 3900 (see taas_id, vlan_range_start default value)

``br-tap``

::

  table=1,  priority=1,dl_vlan=3900  actions=IN_PORT
  table=2,  priority=1,dl_vlan=3900  actions=output:"patch-tap-int"

* VLAN 3900 (see taas_id, vlan_range_start default value)

Create tap flow
~~~~~~~~~~~~~~~

The used command:

.. code-block:: console

  $ openstack tap flow create --name tap_flow0 --port port0 --tap-service tap_service --direction BOTH

``br-int``

::

  table=0,   priority=20,dl_dst=fa:16:3e:fc:c5:71   actions=NORMAL,mod_vlan_vid:3900,output:"patch-int-tap"
  table=0,   priority=20,in_port="tap4bd58b41-2b"   actions=NORMAL,mod_vlan_vid:3900,output:"patch-int-tap"

* fa:16:3e:fc:c5:71 : mac address of the port associated with the tap flow
* tap4bd58b41-2b: tap port id in br-int for the port associated with the tap flow

``br-tun``

::

  table=3,   priority=1,tun_id=0xf3c  actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID[0..11]->NXM_OF_VLAN_TCI[0..11],resubmit(,35)
  table=4,   priority=1,tun_id=0xf3c  actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID[0..11]->NXM_OF_VLAN_TCI[0..11],resubmit(,35)
  table=6,   priority=1,tun_id=0xf3c  actions=move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID[0..11]->NXM_OF_VLAN_TCI[0..11],resubmit(,35)
  table=37,  priority=1,tun_id=0xf3c  actions=resubmit(,39)

From learn action (see table 39):

::

  table=30,  priority=1,vlan_tci=0x0f3c/0x0fff   actions=load:0xf3c->NXM_NX_TUN_ID[0..11],load:0->NXM_OF_VLAN_TCI[0..11],output:

* table 3: GRE_TUN_TO_LV
* table 4: VXLAN_TUN_TO_LV
* table 6: GENEVE_TUN_TO_LV
* table 30: TAAS_SEND_UCAST
* table 37: TAAS_SRC_CHECK
* table 39: TAAS_SRC_RESPOND
* tun_id=0xf3c => VLAN 3900 (see taas_id, vlan_range_start default value)
* port 3: vxlan port on the host


.. [1] `<https://opendev.org/openstack/tap-as-a-service/src/commit/c919ccd485060ec0511dda559c220f81b790c41c/neutron_taas/services/taas/drivers/linux/ovs_constants.py#L21-L28>`_
.. [2] `<https://opendev.org/openstack/tap-as-a-service/src/commit/c919ccd485060ec0511dda559c220f81b790c41c/neutron_taas/services/taas/drivers/linux/ovs_constants.py#L17-L19>`_
.. [3] `<https://opendev.org/openstack/tap-as-a-service/src/commit/c919ccd485060ec0511dda559c220f81b790c41c/neutron_taas/extensions/taas.py#L133-L142>`_
