# Copyright 2016 VMware, Inc.
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

from neutron.db.migration import cli


"""initial Newton no op contract script

Revision ID: 80c85b675b6e
Revises: start_neutron_taas
Create Date: 2016-05-06 04:58:04.510568

"""


# revision identifiers, used by Alembic.
revision = '80c85b675b6e'
down_revision = 'start_neutron_taas'
branch_labels = (cli.CONTRACT_BRANCH,)


def upgrade():
    pass
