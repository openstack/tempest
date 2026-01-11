# Copyright 2018 OpenStack Foundation
# All Rights Reserved.
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

from tempest.api.network import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class AgentManagementNegativeTest(base.BaseNetworkTest):

    credentials = ['primary', 'project_reader']

    @classmethod
    def setup_clients(cls):
        super(AgentManagementNegativeTest, cls).setup_clients()
        if CONF.enforce_scope.neutron:
            cls.reader_client = cls.os_project_reader.network_agents_client
        else:
            cls.reader_client = cls.agents_client

    @decorators.idempotent_id('e335be47-b9a1-46fd-be30-0874c0b751e6')
    @decorators.attr(type=['negative'])
    def test_list_agents_non_admin(self):
        """Validate that non-admin user cannot list agents."""
        # Listing agents requires admin_only permissions.
        body = self.reader_client.list_agents()
        self.assertEmpty(body["agents"])
