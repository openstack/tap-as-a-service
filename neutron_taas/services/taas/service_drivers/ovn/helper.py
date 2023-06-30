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

import queue
import threading

from neutron.conf.plugins.ml2.drivers.ovn import ovn_conf
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from ovs.stream import Stream

from neutron_taas.services.taas.service_drivers.ovn.ovsdb import impl_idl_taas


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class TaasOvnProviderHelper():

    def __init__(self):
        ovn_conf.register_opts()
        self._requests = queue.Queue()
        self._helper_thread = threading.Thread(target=self._request_handler)
        self._helper_thread.daemon = True
        self._check_and_set_ssl_files()
        self._taas_mirror_func_map = {
            'mirror_del': self.mirror_del,
            'mirror_add': self.mirror_add,
        }
        self._subscribe()
        self._helper_thread.start()

    def _subscribe(self):
        registry.subscribe(self._post_fork_initialize,
                           resources.PROCESS,
                           events.AFTER_INIT)

    def _post_fork_initialize(self, resource, event, trigger, payload=None):
        self.ovn_nbdb = impl_idl_taas.OvnNbIdlForTaas()
        self.ovn_nbdb_api = self.ovn_nbdb.start()

    def _check_and_set_ssl_files(self):
        priv_key_file = CONF.ovn.ovn_nb_private_key
        cert_file = CONF.ovn.ovn_nb_certificate
        ca_cert_file = CONF.ovn.ovn_nb_ca_cert

        if priv_key_file:
            Stream.ssl_set_private_key_file(priv_key_file)

        if cert_file:
            Stream.ssl_set_certificate_file(cert_file)

        if ca_cert_file:
            Stream.ssl_set_ca_cert_file(ca_cert_file)

    def _request_handler(self):
        while True:
            request = self._requests.get()
            request_type = request['type']
            if request_type == 'exit':
                break

            request_handler = self._taas_mirror_func_map.get(request_type)
            try:
                if request_handler:
                    request_handler(request['info'])
                self._requests.task_done()
            except Exception:
                # If any unexpected exception happens we don't want the
                # notify_loop to exit.
                LOG.exception('Unexpected exception in request_handler')

    def _execute_commands(self, commands):
        with self.ovn_nbdb_api.transaction(check_error=True) as txn:
            for command in commands:
                txn.add(command)

    def shutdown(self):
        self._requests.put({'type': 'exit'})
        self._helper_thread.join()
        self.ovn_nbdb.stop()
        del self.ovn_nbdb_api

    def add_request(self, req):
        self._requests.put(req)

    @log_helpers.log_method_call
    def mirror_del(self, request):
        port_id = request.pop('port_id')
        ovn_port = self.ovn_nbdb_api.lookup('Logical_Switch_Port', port_id)
        mirror = self.ovn_nbdb_api.mirror_get(
            request['name']).execute(check_error=True)
        self.ovn_nbdb_api.lsp_detach_mirror(
            ovn_port.name, mirror.uuid,
            if_exist=True).execute(check_error=True)
        self.ovn_nbdb_api.mirror_del(
            mirror.uuid).execute(check_error=True)

    @log_helpers.log_method_call
    def mirror_add(self, request):
        port_id = request.pop('port_id')
        ovn_port = self.ovn_nbdb_api.lookup('Logical_Switch_Port', port_id)

        mirror = self.ovn_nbdb_api.mirror_add(
            **request).execute(check_error=True)
        self.ovn_nbdb_api.lsp_attach_mirror(
            ovn_port.name, mirror.uuid,
            may_exist=True).execute(check_error=True)

        return mirror
