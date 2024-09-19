========================
DevStack external plugin
========================

A `local.conf` recipe to enable tap-as-a-service::

    [[local|localrc]]
    enable_plugin tap-as-a-service https://opendev.org/openstack/tap-as-a-service
    enable_service taas

To enable mirroring via GRE or ERSPAN tunnels::

    [[local|localrc]]
    enable_plugin tap-as-a-service https://opendev.org/openstack/tap-as-a-service
    enable_service taas
    enable_service tap_mirror

To enable the mirroring with OVS driver::

    TAAS_SERVICE_DRIVER=TAAS:TAAS:neutron_taas.services.taas.service_drivers.taas_rpc.TaasRpcDriver:default

To enable mirroring with OVN driver::

    TAAS_SERVICE_DRIVER=TAAS:TAAS:neutron_taas.services.taas.service_drivers.ovn.taas_ovn.TaasOvnDriver:default
