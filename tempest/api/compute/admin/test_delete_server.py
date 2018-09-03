# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest.common import waiters
from tempest.lib import decorators


class DeleteServersAdminTestJSON(base.BaseV2ComputeAdminTest):
    # NOTE: Server creations of each test class should be under 10
    # for preventing "Quota exceeded for instances".

    @classmethod
    def setup_clients(cls):
        super(DeleteServersAdminTestJSON, cls).setup_clients()
        cls.non_admin_client = cls.servers_client
        cls.admin_client = cls.os_admin.servers_client

    @decorators.idempotent_id('99774678-e072-49d1-9d2a-49a59bc56063')
    def test_delete_server_while_in_error_state(self):
        # Delete a server while it's VM state is error
        server = self.create_test_server(wait_until='ACTIVE')
        self.admin_client.reset_state(server['id'], state='error')
        # Verify server's state
        server = self.non_admin_client.show_server(server['id'])['server']
        self.assertEqual(server['status'], 'ERROR')
        self.non_admin_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client,
                                            server['id'],
                                            ignore_error=True)

    @decorators.idempotent_id('73177903-6737-4f27-a60c-379e8ae8cf48')
    def test_admin_delete_servers_of_others(self):
        # Administrator can delete servers of others
        server = self.create_test_server(wait_until='ACTIVE')
        self.admin_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])
