# Copyright (C) 2018 AT&T
# Copyright (C) 2015 Ericsson AB
# Copyright (c) 2015 Gigamon
#
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
from sqlalchemy import orm
from sqlalchemy.orm import exc

from neutron.db.models import segment
from neutron_lib import constants
from neutron_lib.db import api as db_api
from neutron_lib.db import model_base
from neutron_lib.db import model_query
from neutron_lib.db import utils as db_utils
from neutron_lib.exceptions import taas as taas_exc
from neutron_lib.plugins import directory
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import uuidutils

from neutron_taas.extensions import taas as taas_extension

LOG = logging.getLogger(__name__)


class TapService(model_base.BASEV2, model_base.HasId,
                 model_base.HasProjectNoIndex):

    # Represents a V2 TapService Object
    __tablename__ = 'tap_services'
    name = sa.Column(sa.String(255), nullable=True)
    description = sa.Column(sa.String(1024), nullable=True)
    port_id = sa.Column(sa.String(36), nullable=False)
    status = sa.Column(sa.String(16), nullable=False,
                       server_default=constants.ACTIVE)


class TapFlow(model_base.BASEV2, model_base.HasId,
              model_base.HasProjectNoIndex):

    # Represents a V2 TapFlow Object
    __tablename__ = 'tap_flows'
    name = sa.Column(sa.String(255), nullable=True)
    description = sa.Column(sa.String(1024), nullable=True)
    tap_service_id = sa.Column(sa.String(36),
                               sa.ForeignKey("tap_services.id",
                                             ondelete="CASCADE"),
                               nullable=False)
    source_port = sa.Column(sa.String(36), nullable=False)
    direction = sa.Column(sa.Enum('IN', 'OUT', 'BOTH',
                                  name='tapflows_direction'),
                          nullable=False)
    status = sa.Column(sa.String(16), nullable=False,
                       server_default=constants.ACTIVE)
    vlan_filter = sa.Column(sa.String(1024), nullable=True)


class TapIdAssociation(model_base.BASEV2):

    # Internal mapping between a TAP Service and
    # id to be used by the Agents
    __tablename__ = 'tap_id_associations'
    tap_service_id = sa.Column(sa.String(36),
                               sa.ForeignKey("tap_services.id",
                                             ondelete='SET NULL'),
                               nullable=True)
    taas_id = sa.Column(sa.Integer, primary_key=True, unique=True)
    tap_service = orm.relationship(
        TapService,
        backref=orm.backref("tap_service_id",
                            lazy="joined"),
        primaryjoin='TapService.id==TapIdAssociation.tap_service_id')


class Taas_db_Mixin(taas_extension.TaasPluginBase):

    def _core_plugin(self):
        return directory.get_plugin()

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_READER
    def _get_tap_service(self, context, id):
        try:
            return model_query.get_by_id(context, TapService, id)
        except exc.NoResultFound:
            raise taas_exc.TapServiceNotFound(tap_id=id)

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_READER
    def _get_tap_id_association(self, context, tap_service_id):
        try:
            query = model_query.query_with_hooks(context, TapIdAssociation)
            return query.filter(TapIdAssociation.tap_service_id ==
                                tap_service_id).one()
        except exc.NoResultFound:
            raise taas_exc.TapServiceNotFound(tap_id=tap_service_id)

    @db_api.CONTEXT_READER
    def _get_tap_flow(self, context, id):
        try:
            return model_query.get_by_id(context, TapFlow, id)
        except exc.NoResultFound:
            raise taas_exc.TapFlowNotFound(flow_id=id)

    def _make_tap_service_dict(self, tap_service, fields=None):
        res = {'id': tap_service['id'],
               'tenant_id': tap_service['tenant_id'],
               'name': tap_service['name'],
               'description': tap_service['description'],
               'port_id': tap_service['port_id'],
               'status': tap_service['status']}

        return db_utils.resource_fields(res, fields)

    def _make_tap_id_association_dict(self, tap_id_association):
        res = {'tap_service_id': tap_id_association['tap_service_id'],
               'taas_id': tap_id_association['taas_id']}

        return res

    def _make_tap_flow_dict(self, tap_flow, fields=None):
        res = {'id': tap_flow['id'],
               'tenant_id': tap_flow['tenant_id'],
               'tap_service_id': tap_flow['tap_service_id'],
               'name': tap_flow['name'],
               'description': tap_flow['description'],
               'source_port': tap_flow['source_port'],
               'direction': tap_flow['direction'],
               'status': tap_flow['status'],
               'vlan_filter': tap_flow['vlan_filter']}

        return db_utils.resource_fields(res, fields)

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_READER
    def get_port_network_data(self, context, port):
        ns = context.session.query(
            segment.NetworkSegment.network_id,
            segment.NetworkSegment.physical_network,
            segment.NetworkSegment.network_type
        ).filter(
            segment.NetworkSegment.network_id == port['network_id']
        ).first()

        if not ns:
            LOG.debug("No Network Segment found for network_id %s",
                      port['network_id'])
            return

        ns_data = {
            'physical_network': ns[1],
            'network_type': ns[2]
        }
        return ns_data

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_WRITER
    def create_tap_service(self, context, tap_service):
        LOG.debug("create_tap_service() called")
        t_s = tap_service['tap_service']
        tenant_id = t_s['tenant_id']
        tap_service_db = TapService(
            id=uuidutils.generate_uuid(),
            tenant_id=tenant_id,
            name=t_s['name'],
            description=t_s['description'],
            port_id=t_s['port_id'],
            status=constants.DOWN,
        )
        context.session.add(tap_service_db)

        return self._make_tap_service_dict(tap_service_db)

    def _rebuild_taas_id_allocation_range(self, context):
        query = context.session.query(
            TapIdAssociation).all()

        allocate_taas_id_list = [_q.taas_id for _q in query]
        first_taas_id = cfg.CONF.taas.vlan_range_start
        # Exclude range end
        last_taas_id = cfg.CONF.taas.vlan_range_end
        all_taas_id_set = set(range(first_taas_id, last_taas_id))
        vaild_taas_id_set = all_taas_id_set - set(allocate_taas_id_list)

        for _id in vaild_taas_id_set:
            # new taas id
            context.session.add(TapIdAssociation(
                taas_id=_id))

    def _allocate_taas_id_with_tap_service_id(self, context, tap_service_id):
        query = context.session.query(TapIdAssociation).filter_by(
            tap_service_id=None).first()
        if not query:
            self._rebuild_taas_id_allocation_range(context)
            # try again
            query = context.session.query(TapIdAssociation).filter_by(
                tap_service_id=None).first()

        if query:
            query.update({"tap_service_id": tap_service_id})
            return query
        # not found
        raise taas_exc.TapServiceLimitReached()

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_WRITER
    def create_tap_id_association(self, context, tap_service_id):
        LOG.debug("create_tap_id_association() called")
        # create the TapIdAssociation object
        # allocate Taas id.
        # if conflict happened, it will raise db.DBDuplicateEntry.
        # this will be retry request again in neutron controller framework.
        # so we just make sure TapIdAssociation field taas_id is unique
        tap_id_association_db = self._allocate_taas_id_with_tap_service_id(
            context, tap_service_id)

        return self._make_tap_id_association_dict(tap_id_association_db)

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_WRITER
    def create_tap_flow(self, context, tap_flow):
        LOG.debug("create_tap_flow() called")
        t_f = tap_flow['tap_flow']
        tenant_id = t_f['tenant_id']
        # TODO(Vinay): Check for the tenant_id validation
        # TODO(Vinay): Check for the source port validation
        tap_flow_db = TapFlow(
            id=uuidutils.generate_uuid(),
            tenant_id=tenant_id,
            name=t_f['name'],
            description=t_f['description'],
            tap_service_id=t_f['tap_service_id'],
            source_port=t_f['source_port'],
            direction=t_f['direction'],
            status=constants.DOWN,
            vlan_filter=t_f['vlan_filter'],
        )
        context.session.add(tap_flow_db)

        return self._make_tap_flow_dict(tap_flow_db)

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_WRITER
    def delete_tap_service(self, context, id):
        LOG.debug("delete_tap_service() called")

        count = context.session.query(TapService).filter_by(id=id).delete()

        if not count:
            raise taas_exc.TapServiceNotFound(tap_id=id)

    @db_api.CONTEXT_WRITER
    def delete_tap_flow(self, context, id):
        LOG.debug("delete_tap_flow() called")
        count = context.session.query(TapFlow).filter_by(id=id).delete()

        if not count:
            raise taas_exc.TapFlowNotFound(flow_id=id)

    def get_tap_service(self, context, id, fields=None):
        LOG.debug("get_tap_service() called")

        t_s = self._get_tap_service(context, id)
        return self._make_tap_service_dict(t_s, fields)

    def get_tap_id_association(self, context, tap_service_id):
        LOG.debug("get_tap_id_association() called")

        t_a = self._get_tap_id_association(context, tap_service_id)
        return self._make_tap_id_association_dict(t_a)

    @db_api.CONTEXT_READER
    def get_tap_flow(self, context, id, fields=None):
        LOG.debug("get_tap_flow() called")

        t_f = self._get_tap_flow(context, id)
        return self._make_tap_flow_dict(t_f, fields)

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_READER
    def get_tap_services(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        LOG.debug("get_tap_services() called")
        return model_query.get_collection(context, TapService,
                                          self._make_tap_service_dict,
                                          filters=filters, fields=fields)

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_READER
    def get_tap_flows(self, context, filters=None, fields=None,
                      sorts=None, limit=None, marker=None,
                      page_reverse=False):
        LOG.debug("get_tap_flows() called")
        return model_query.get_collection(context, TapFlow,
                                          self._make_tap_flow_dict,
                                          filters=filters, fields=fields)

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_READER
    def get_port_details(self, context, port_id):
        port = self._core_plugin().get_port(context, port_id)

        return port

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_WRITER
    def update_tap_service(self, context, id, tap_service):
        LOG.debug("update_tap_service() called")
        t_s = tap_service['tap_service']
        tap_service_db = self._get_tap_service(context, id)
        tap_service_db.update(t_s)
        return self._make_tap_service_dict(tap_service_db)

    @db_api.retry_if_session_inactive()
    @db_api.CONTEXT_WRITER
    def update_tap_flow(self, context, id, tap_flow):
        LOG.debug("update_tap_flow() called")
        t_f = tap_flow['tap_flow']
        tap_flow_db = self._get_tap_flow(context, id)
        tap_flow_db.update(t_f)
        return self._make_tap_flow_dict(tap_flow_db)
