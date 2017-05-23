# Copyright 2013 IBM Corp
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
from tempest.common import compute
from tempest.lib import decorators


class MultipleCreateTestJSON(base.BaseV2ComputeTest):

    @decorators.idempotent_id('61e03386-89c3-449c-9bb1-a06f423fd9d1')
    def test_multiple_create(self):
        tenant_network = self.get_tenant_network()
        body, servers = compute.create_test_server(
            self.os_primary,
            wait_until='ACTIVE',
            min_count=2,
            tenant_network=tenant_network)
        for server in servers:
            self.addCleanup(self.servers_client.delete_server, server['id'])
        # NOTE(maurosr): do status response check and also make sure that
        # reservation_id is not in the response body when the request send
        # contains return_reservation_id=False
        self.assertNotIn('reservation_id', body)
        self.assertEqual(2, len(servers))

    @decorators.idempotent_id('864777fb-2f1e-44e3-b5b9-3eb6fa84f2f7')
    def test_multiple_create_with_reservation_return(self):
        body = self.create_test_server(wait_until='ACTIVE',
                                       min_count=1,
                                       max_count=2,
                                       return_reservation_id=True)
        self.assertIn('reservation_id', body)
