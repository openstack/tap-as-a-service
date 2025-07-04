#!/bin/bash

# Copyright 2015 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script is meant to be sourced from devstack.  It is a wrapper of
# devmido scripts that allows proper exporting of environment variables.


function install_taas {
    setup_develop $NEUTRON_TAAS_DIR
}

function generate_taas_config_files {
    # Uses oslo config generator to generate TaaS sample configuration files
    (cd $NEUTRON_TAAS_DIR && exec ./tools/generate_config_file_samples.sh)
}

function configure_taas_plugin {
    echo "Configuring taas"
    cp $NEUTRON_TAAS_DIR/etc/taas_plugin.ini.sample $TAAS_PLUGIN_CONF_FILE
    neutron_server_config_add $TAAS_PLUGIN_CONF_FILE
    neutron_service_plugin_class_add taas
    if is_service_enabled tap_mirror; then
        neutron_service_plugin_class_add tapmirror
    fi
    inicomment $TAAS_PLUGIN_CONF_FILE service_providers service_provider
    iniadd $TAAS_PLUGIN_CONF_FILE service_providers service_provider $TAAS_SERVICE_DRIVER
}

function configure_taas_agent {
    echo "Configuring taas agent"
    source $NEUTRON_DIR/devstack/lib/l2_agent
    plugin_agent_add_l2_agent_extension taas
    configure_l2_agent
}

if is_service_enabled taas; then
    if [[ "$1" == "stack" ]]; then
        if [[ "$2" == "pre-install" ]]; then
            :
        elif [[ "$2" == "install" ]]; then
            install_taas
        elif [[ "$2" == "post-config" ]]; then
            generate_taas_config_files
            configure_taas_plugin
            if is_service_enabled q-svc neutron-api; then
                neutron-db-manage --subproject tap-as-a-service upgrade head
            fi
        elif [[ "$2" == "extra" ]]; then
            :
        fi
    elif [[ "$1" == "unstack" ]]; then
        :
    fi
fi

if is_service_enabled q-agt neutron-agent; then
    if [[ "$1" == "stack" ]]; then
        if [[ "$2" == "pre-install" ]]; then
            :
        elif [[ "$2" == "install" ]]; then
            install_taas
        elif [[ "$2" == "post-config" ]]; then
            if is_service_enabled q-agt neutron-agent; then
                configure_taas_agent
            fi
        elif [[ "$2" == "extra" ]]; then
            :
        fi
    elif [[ "$1" == "unstack" ]]; then
        :
    fi
fi
