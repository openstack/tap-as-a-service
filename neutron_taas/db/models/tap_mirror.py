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

from neutron_lib.api.definitions import tap_mirror as mirror_extension
from neutron_lib.db import constants as db_const
from neutron_lib.db import model_base


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
