# All Rights Reserved 2020
#
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

import logging

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils
from osc_lib.utils import columns as column_util

from neutronclient._i18n import _
from neutronclient.neutron import v2_0 as neutronv20
from neutronclient.osc import utils as nc_osc_utils


LOG = logging.getLogger(__name__)

TAP_SERVICE = 'tap_service'
TAP_SERVICES = '%ss' % TAP_SERVICE

path = 'taas'
object_path = '/%s/' % path
resource_path = '/%s/%%s/%%s' % path

_attr_map = (
    ('id', 'ID', column_util.LIST_BOTH),
    ('tenant_id', 'Tenant', column_util.LIST_LONG_ONLY),
    ('name', 'Name', column_util.LIST_BOTH),
    ('port_id', 'Port', column_util.LIST_BOTH),
    ('status', 'Status', column_util.LIST_BOTH),
)


def _add_updatable_args(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this Tap service.'))
    parser.add_argument(
        '--description',
        help=_('Description for this Tap service.'))


def _updatable_args2body(parsed_args, body):
    neutronv20.update_dict(parsed_args, body, ['name', 'description'])


class CreateTapService(command.ShowOne):
    _description = _("Create a tap service")

    def get_parser(self, prog_name):
        parser = super(CreateTapService, self).get_parser(prog_name)
        nc_osc_utils.add_project_owner_option_to_parser(parser)
        _add_updatable_args(parser)
        parser.add_argument(
            '--port',
            dest='port_id',
            required=True,
            metavar="PORT",
            help=_('Port to which the Tap service is connected.'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        attrs = {}
        if parsed_args.name is not None:
            attrs['name'] = str(parsed_args.name)
        if parsed_args.description is not None:
            attrs['description'] = str(parsed_args.description)
        if parsed_args.port_id is not None:
            port_id = client.find_resource('port', parsed_args.port_id)['id']
            attrs['port_id'] = port_id
        if 'project' in parsed_args and parsed_args.project is not None:
            project_id = nc_osc_utils.find_project(
                self.app.client_manager.identity,
                parsed_args.project,
                parsed_args.project_domain,
            ).id
            attrs['tenant_id'] = project_id
        body = {TAP_SERVICE: attrs}
        obj = client.post('%s%s' % (object_path, TAP_SERVICES),
                          body=body)[TAP_SERVICE]
        columns, display_columns = column_util.get_columns(obj, _attr_map)
        data = osc_utils.get_dict_properties(obj, columns)
        return display_columns, data


class ListTapService(command.Lister):
    _description = _("List tap services that belong to a given tenant")

    def get_parser(self, prog_name):
        parser = super(ListTapService, self).get_parser(prog_name)
        nc_osc_utils.add_project_owner_option_to_parser(parser)

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        params = {}
        if parsed_args.project is not None:
            project_id = nc_osc_utils.find_project(
                self.app.client_manager.identity,
                parsed_args.project,
                parsed_args.project_domain,
            ).id
            params['tenant_id'] = project_id
        objs = client.list(TAP_SERVICES, '%s%s' % (object_path, TAP_SERVICES),
                           retrieve_all=True, params=params)[TAP_SERVICES]
        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=True)
        return (headers, (osc_utils.get_dict_properties(
            s, columns) for s in objs))


class ShowTapService(command.ShowOne):
    _description = _("Show information of a given tap service")

    def get_parser(self, prog_name):
        parser = super(ShowTapService, self).get_parser(prog_name)
        parser.add_argument(
            TAP_SERVICE,
            metavar="<%s>" % TAP_SERVICE,
            help=_("ID or name of tap service to look up."),
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        id = client.find_resource(TAP_SERVICE, parsed_args.tap_service)['id']
        obj = client.get(resource_path % (TAP_SERVICES, id))[TAP_SERVICE]
        columns, display_columns = column_util.get_columns(obj, _attr_map)
        data = osc_utils.get_dict_properties(obj, columns)
        return display_columns, data


class DeleteTapService(command.Command):
    _description = _("Delete a tap service")

    def get_parser(self, prog_name):
        parser = super(DeleteTapService, self).get_parser(prog_name)
        parser.add_argument(
            TAP_SERVICE,
            metavar="<%s>" % TAP_SERVICE,
            nargs="+",
            help=_("ID(s) or name(s) of tap service to delete."),
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        fails = 0
        for id_or_name in parsed_args.tap_service:
            try:
                id = client.find_resource(TAP_SERVICE, id_or_name)['id']
                client.delete(resource_path % (TAP_SERVICES, id))
                LOG.warning("Tap service %(id)s deleted", {'id': id})
            except Exception as e:
                fails += 1
                LOG.error("Failed to delete tap service with name or ID "
                          "'%(id_or_name)s': %(e)s",
                          {'id_or_name': id_or_name, 'e': e})
        if fails > 0:
            msg = (_("Failed to delete %(fails)s of %(total)s tap service.") %
                   {'fails': fails, 'total': len(parsed_args.tap_service)})
            raise exceptions.CommandError(msg)


class UpdateTapService(command.ShowOne):
    _description = _("Update a tap service.")

    def get_parser(self, prog_name):
        parser = super(UpdateTapService, self).get_parser(prog_name)
        parser.add_argument(
            TAP_SERVICE,
            metavar="<%s>" % TAP_SERVICE,
            help=_("ID or name of tap service to update."),
        )
        _add_updatable_args(parser)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        id = client.find_resource(TAP_SERVICE, parsed_args.tap_service)['id']
        attrs = {}
        if parsed_args.name is not None:
            attrs['name'] = str(parsed_args.name)
        if parsed_args.description is not None:
            attrs['description'] = str(parsed_args.description)
        body = {TAP_SERVICE: attrs}
        obj = client.put(resource_path % (TAP_SERVICES, id), body)[TAP_SERVICE]
        columns, display_columns = column_util.get_columns(obj, _attr_map)
        data = osc_utils.get_dict_properties(obj, columns)
        return display_columns, data
