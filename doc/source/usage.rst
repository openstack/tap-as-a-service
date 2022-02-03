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

Usage Workflow
==============

1. Create a Neutron port with 'port_security_enabled' set to 'false'.

.. note::

   If you already have a port attached to a virtual machine you can
   disable port-security on that port and use that for mirroring also.

.. code-block:: console

 $ openstack port create port_tap_service --disable-port-security

2. Launch a VM (VM on which you want to monitor/receive the mirrored data).
   Associate the Neutron port created in step 1 while creating the VM.

.. note::

   To capture and analize traffic it is suggested to use VM image that has
   advanced tools like tcpdump.

.. code-block:: console

  $ openstack server create --nic port-id=port_tap_service monitor_vm

3. Using Openstack Client command for TaaS **openstack tap service create** or
   via REST APIs create a Tap Service instance by associating the port
   created in step 1.

.. code-block:: console

  $ openstack tap service create --name ts_0 --port port_tap_service

4. Using Openstack Client command for TaaS **openstack tap flow create** or
   via REST APIs create a Tap Flow instance by associating the Tap Service
   instance created in step 3 and the target Neutron port from which you want
   to mirror traffic (assuming the Neutron port from which the traffic
   needs to be monitored already exists.)
   Mirroring can be done for both incoming and/or outgoing traffic from the
   target Neutron port.

.. code-block:: console

  $ openstack tap flow create --name tf_0 --port source_port --tap-service ts_0 --direction BOTH

5. Observe the mirrored traffic on the monitoring VM by running tools such as
   tcpdump.
