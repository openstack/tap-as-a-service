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

import atexit
import contextlib
import tenacity

from neutron.common.ovn import exceptions as ovn_exceptions
from neutron.conf.plugins.ml2.drivers.ovn import ovn_conf
from neutron_lib import exceptions as n_exc
from oslo_config import cfg
from oslo_log import log
from ovsdbapp.backend import ovs_idl
from ovsdbapp.backend.ovs_idl import connection
from ovsdbapp.backend.ovs_idl import idlutils
from ovsdbapp.backend.ovs_idl import transaction as idl_trans
from ovsdbapp.schema.ovn_northbound import impl_idl as nb_impl_idl


LOG = log.getLogger(__name__)
CONF = cfg.CONF


class Backend(ovs_idl.Backend):
    lookup_table = {}
    ovsdb_connection = None

    def __init__(self, connection):
        ovn_conf.register_opts()
        self.ovsdb_connection = connection
        super().__init__(connection)

    def start_connection(self, connection):
        try:
            self.ovsdb_connection.start()
        except Exception as e:
            connection_exception = OvsdbConnectionUnavailable(
                db_schema=self.schema, error=e)
            LOG.exception(connection_exception)
            raise connection_exception from e

    @property
    def idl(self):
        return self.ovsdb_connection.idl

    @property
    def tables(self):
        return self.idl.tables

    _tables = tables

    def is_table_present(self, table_name):
        return table_name in self._tables

    def is_col_present(self, table_name, col_name):
        return self.is_table_present(table_name) and (
            col_name in self._tables[table_name].columns)

    def create_transaction(self, check_error=False, log_errors=True):
        return idl_trans.Transaction(
            self, self.ovsdb_connection, self.ovsdb_connection.timeout,
            check_error, log_errors)

    # Check for a column match in the table. If not found do a retry with
    # a stop delay of 10 secs. This function would be useful if the caller
    # wants to verify for the presence of a particular row in the table
    # with the column match before doing any transaction.
    # Eg. We can check if Logical_Switch row is present before adding a
    # logical switch port to it.
    @tenacity.retry(retry=tenacity.retry_if_exception_type(RuntimeError),
                    wait=tenacity.wait_exponential(),
                    stop=tenacity.stop_after_delay(10),
                    reraise=True)
    def check_for_row_by_value_and_retry(self, table, column, match):
        try:
            idlutils.row_by_value(self.idl, table, column, match)
        except idlutils.RowNotFound as e:
            msg = (_("%(match)s does not exist in %(column)s of %(table)s")
                   % {'match': match, 'column': column, 'table': table})
            raise RuntimeError(msg) from e


class OvsdbConnectionUnavailable(n_exc.ServiceUnavailable):
    message = _("OVS database connection to %(db_schema)s failed with error: "
                "'%(error)s'. Verify that the OVS and OVN services are "
                "available and that the 'ovn_nb_connection' and "
                "'ovn_sb_connection' configuration options are correct.")


class OvsdbNbOvnIdl(nb_impl_idl.OvnNbApiIdlImpl, Backend):
    def __init__(self, connection):
        super().__init__(connection)
        self.idl._session.reconnect.set_probe_interval(
            ovn_conf.get_ovn_ovsdb_probe_interval())

    @contextlib.contextmanager
    def transaction(self, check_error=False, log_errors=True, nested=True,
                    **kwargs):
        """A wrapper on the ovsdbapp transaction to work with revisions.

        This method is just a wrapper around the ovsdbapp transaction
        to handle revision conflicts correctly.
        """
        try:
            with super().transaction(check_error, log_errors, nested,
                                     **kwargs) as t:
                yield t
        except ovn_exceptions.RevisionConflict as e:
            LOG.info('Transaction aborted. Reason: %s', e)


class OvnNbIdlForTaas(connection.OvsdbIdl):

    SCHEMA = "OVN_Northbound"
    TABLES = ('Logical_Switch_Port', 'Mirror')

    def __init__(self):
        ovn_conf.register_opts()
        self.conn_string = ovn_conf.get_ovn_nb_connection()
        helper = self._get_ovsdb_helper(self.conn_string)
        for table in OvnNbIdlForTaas.TABLES:
            helper.register_table(table)
        super().__init__(self.conn_string, helper)
        atexit.register(self.stop)

    @tenacity.retry(
        wait=tenacity.wait_exponential(18),
        reraise=True)
    def _get_ovsdb_helper(self, connection_string):
        return idlutils.get_schema_helper(connection_string, self.SCHEMA)

    def start(self):
        self.conn = connection.Connection(self, timeout=180)
        return OvsdbNbOvnIdl(self.conn)

    def stop(self):
        # Close the running connection if it has been initalized
        if hasattr(self, 'conn'):
            if not self.conn.stop(timeout=180):
                LOG.debug("Connection terminated to OvnNb "
                          "but a thread is still alive")
            del self.conn
        # Close the idl session
        self.close()
