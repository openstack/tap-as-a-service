# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import sqlalchemy as sa
from sqlalchemy.orm import exc

from neutron_lib.api.definitions import tap_mirror as mirror_extension
from neutron_lib.db import api as db_api
from neutron_lib.db import constants as db_const
from neutron_lib.db import model_base
from neutron_lib.db import model_query
from neutron_lib.db import utils as db_utils
from neutron_lib.exceptions import taas as taas_exc
from neutron_lib.plugins import directory
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_serialization import jsonutils
from oslo_utils import uuidutils

from neutron_taas.extensions import tap_mirror as tap_m_extension

LOG = logging.getLogger(__name__)


class TapMirror(model_base.BASEV2, model_base.HasId,
                model_base.HasProjectNoIndex):
    """Represents a Tap Mirror

    A Tap Mirror can be a GRE or ERSPAN tunnel representation.
    """

    __tablename__ = 'tap_mirrors'

    name = sa.Column(sa.String(db_const.NAME_FIELD_SIZE))
    description = sa.Column(sa.String(db_const.DESCRIPTION_FIELD_SIZE))
    port_id = sa.Column(sa.String(db_const.UUID_FIELD_SIZE),
                        nullable=False)
    directions = sa.Column(sa.String(255), nullable=False)
    remote_ip = sa.Column(sa.String(db_const.IP_ADDR_FIELD_SIZE),
                          nullable=False)
    mirror_type = sa.Column(sa.Enum('erspanv1', 'gre',
                                    name='tapmirrors_type'),
                            nullable=False)
    api_collections = [mirror_extension.COLLECTION_NAME]
    collection_resource_map = {
        mirror_extension.COLLECTION_NAME: mirror_extension.RESOURCE_NAME}


class Taas_mirror_db_mixin(tap_m_extension.TapMirrorBase):

    def _make_tap_mirror_dict(self, tap_mirror, fields=None):
        res = {
            'id': tap_mirror.get('id'),
            'project_id': tap_mirror.get('project_id'),
            'name': tap_mirror.get('name'),
            'description': tap_mirror.get('description'),
            'port_id': tap_mirror.get('port_id'),
            'directions': jsonutils.loads(tap_mirror.get('directions')),
            'remote_ip': tap_mirror.get('remote_ip'),
            'mirror_type': tap_mirror.get('mirror_type'),
        }
        return db_utils.resource_fields(res, fields)

    @db_api.retry_if_session_inactive()
    def get_port_details(self, context, port_id):
        with db_api.CONTEXT_READER.using(context):
            core_plugin = directory.get_plugin()
            return core_plugin.get_port(context, port_id)

    @db_api.retry_if_session_inactive()
    @log_helpers.log_method_call
    def create_tap_mirror(self, context, tap_mirror):
        fields = tap_mirror['tap_mirror']
        project_id = fields.get('project_id')
        with db_api.CONTEXT_WRITER.using(context):
            tap_mirror_db = TapMirror(
                id=uuidutils.generate_uuid(),
                project_id=project_id,
                name=fields.get('name'),
                description=fields.get('description'),
                port_id=fields.get('port_id'),
                directions=jsonutils.dumps(fields.get('directions')),
                remote_ip=fields.get('remote_ip'),
                mirror_type=fields.get('mirror_type'),
            )
            # TODO(lajoskatona): Check tunnel_id...
            context.session.add(tap_mirror_db)

            return self._make_tap_mirror_dict(tap_mirror_db)

    def _get_tap_mirror(self, context, id):
        with db_api.CONTEXT_READER.using(context):
            try:
                return model_query.get_by_id(context, TapMirror, id)
            except exc.NoResultFound:
                raise taas_exc.TapMirrorNotFound(mirror_id=id)

    @log_helpers.log_method_call
    def get_tap_mirror(self, context, id, fields=None):
        with db_api.CONTEXT_READER.using(context):
            t_m = self._get_tap_mirror(context, id)
            return self._make_tap_mirror_dict(t_m, fields)

    @db_api.retry_if_session_inactive()
    @log_helpers.log_method_call
    def get_tap_mirrors(self, context, filters=None, fields=None,
                        sorts=None, limit=None, marker=None,
                        page_reverse=False):
        with db_api.CONTEXT_READER.using(context):
            return model_query.get_collection(context, TapMirror,
                                              self._make_tap_mirror_dict,
                                              filters=filters, fields=fields)

    @log_helpers.log_method_call
    def delete_tap_mirror(self, context, id):
        with db_api.CONTEXT_WRITER.using(context):
            count = context.session.query(TapMirror).filter_by(id=id).delete()

        if not count:
            raise taas_exc.TapMirrorNotFound(mirror_id=id)

    @db_api.retry_if_session_inactive()
    @log_helpers.log_method_call
    def update_tap_mirror(self, context, id, tap_mirror):
        t_m = tap_mirror['tap_mirror']
        with db_api.CONTEXT_WRITER.using(context):
            tap_mirror_db = self._get_tap_mirror(context, id)
            tap_mirror_db.update(t_m)
            return self._make_tap_mirror_dict(tap_mirror_db)
