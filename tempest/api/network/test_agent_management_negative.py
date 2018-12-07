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
from tempest.lib import decorators


class AgentManagementNegativeTest(base.BaseNetworkTest):

    @decorators.idempotent_id('e335be47-b9a1-46fd-be30-0874c0b751e6')
    @decorators.attr(type=['negative'])
    def test_list_agents_non_admin(self):
        """Validate that non-admin user cannot list agents."""
        # Listing agents requires admin_only permissions.
        body = self.agents_client.list_agents()
        self.assertEmpty(body["agents"])
