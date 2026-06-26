# Copyright 2026 Openinfra Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sqlalchemy as sa
from sqlalchemy import orm

from neutron_lib import constants
from neutron_lib.db import model_base


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
