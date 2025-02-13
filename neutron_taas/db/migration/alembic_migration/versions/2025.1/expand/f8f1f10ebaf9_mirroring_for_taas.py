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

from alembic import op
from neutron_lib.db import constants as db_const

import sqlalchemy as sa


# ERSPAN or GRE mirroring for taas

# Revision ID: f8f1f10ebaf9
# Revises: ccbcc559d175
# Create Date: 2023-05-05 11:59:10.007052

# revision identifiers, used by Alembic.
revision = 'f8f1f10ebaf9'
down_revision = 'ccbcc559d175'


mirror_type_enum = sa.Enum('erspanv1', 'gre', name='tapmirrors_type')


def upgrade():
    op.create_table(
        'tap_mirrors',
        sa.Column('id', sa.String(length=db_const.UUID_FIELD_SIZE),
                  primary_key=True),
        sa.Column('project_id', sa.String(
            length=db_const.PROJECT_ID_FIELD_SIZE), nullable=True),
        sa.Column('name', sa.String(length=db_const.NAME_FIELD_SIZE),
                  nullable=True),
        sa.Column('description', sa.String(
            length=db_const.DESCRIPTION_FIELD_SIZE), nullable=True),
        sa.Column('port_id', sa.String(db_const.UUID_FIELD_SIZE),
                  nullable=False),
        sa.Column('directions', sa.String(255), nullable=False),
        sa.Column('remote_ip', sa.String(db_const.IP_ADDR_FIELD_SIZE)),
        sa.Column('mirror_type', mirror_type_enum, nullable=False)
    )
