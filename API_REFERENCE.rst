==============================
Tap as a Service API REFERENCE
==============================

This documents is an API REFERENCE for Tap-as-a-Service Neutron extension.

The documents is organized into the following sections:
* TaaS Resources
* API Reference
* TaaS CLI Reference
* Workflow

TaaS Resources
==============

TaaS consists of two resources, TapService and TapFlow.

TapService
----------

TapService Represents the port on which the mirrored traffic is delivered.
Any service (VM) that uses the mirrored data is attached to the port.

.. code-block:: python

    'tap_services': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None}, 'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True, 'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'description': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': ''},
        'port_id': {'allow_post': True, 'allow_put': False,
                    'validate': {'type:uuid': None},
                    'is_visible': True},
    }

TapFlow
-------

TapFlow Represents the port from which the traffic needs to be mirrored.

.. code-block:: python

    'tap_flows': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None}, 'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True, 'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'description': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': ''},
        'tap_service_id': {'allow_post': True, 'allow_put': False,
                           'validate': {'type:uuid': None},
                           'required_by_policy': True, 'is_visible': True},
        'source_port': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:uuid': None},
                        'required_by_policy': True, 'is_visible': True},
        'direction': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:values': direction_enum},
                      'is_visible': True},
        'vlan_filter': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:regex_or_none': RANGE_REGEX},
                        'is_visible': True, 'default': None}
    }

    direction_enum = ['IN', 'OUT', 'BOTH']


Multiple TapFlow instances can be associated with a single TapService
instance.

API REFERENCE
=============

https://docs.openstack.org/api-ref/network/v2/index.html#tap-as-a-service

TaaS CLI Reference
==================

Openstack CLI
-------------

OpenStackClient provides
`the basic network commands <https://docs.openstack.org/python-openstackclient/latest/cli/command-list.html>`__
and tap-as-a-service has an extension for taas related commands.

* Create tap service: **openstack tap service create** --name <name of the tap service> --port <name or ID of the port on which the traffic is delivered>

* List tap services: **openstack tap service list**

* Show tap service: **openstack tap service show** <tap service id/tap service name>

* Delete tap service: **openstack tap service delete** <tap service id/tap service name>

* Update tap service: **openstack tap service update** <tap service id/tap service name> --name <new name of the tap service> --description <new description of the tap service>

* Create tap flow: **openstack tap flow create** --name <name of the tap flow> --port <name or ID of the Source port to which the Tap Flow is connected> --tap-service <name or ID of the tap service> --direction <Direction of the Tap flow. Possible options are: IN, OUT, BOTH> --vlan-filter <LAN Ids to be mirrored in the form of range string>

* List tap flows **openstack tap flow list**

* Show tap flow **openstack tap flow show** <tap flow id/tap flow name>

* Delete tap flow **openstack tap flow delete** <tap flow id/tap flow name>

* Update tap flow **openstack tap flow update** <tap flow id/tap flow name> --name <new name of the tap flow> --description <new description of the tap flow>

Workflow
=========

In this section we describe a simple sequence of steps to use TaaS.

Workflow Sequence
------------------

1. Create a Neutron port with 'port_security_enabled' set to 'false'.

2. Launch a VM (VM on which you want to monitor/receive the mirrored data).
   Associate the Neutron port created in step 1 while creating the VM.

3. Using Neutron Client command for TaaS **neutron tap-service-create** or
   via REST APIs create a Tap Service instance by associating the port
   created in step 1.

4. Using Neutron Client command for TaaS **neutron tap-flow-create** or
   via REST APIs create a Tap Flow instance by associating the Tap Service
   instance created in step 3 and the target Neutron port from which you want
   to mirror traffic (assuming the Neutron port from which the traffic
   needs to be monitored already exists.)
   Mirroring can be done for both incoming and/or outgoing traffic from the
   target Neutron port.

5. Observe the mirrored traffic on the monitoring VM by running tools such as
   tcpdump.
