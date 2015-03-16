# Copyright 2013 IBM Corporation
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
from tempest import test


class ServerPasswordTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(ServerPasswordTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServerPasswordTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until="ACTIVE")

    @test.attr(type='gate')
    @test.idempotent_id('f83b582f-62a8-4f22-85b0-0dee50ff783a')
    def test_get_server_password(self):
        self.client.get_password(self.server['id'])

    @test.attr(type='gate')
    @test.idempotent_id('f8229e8b-b625-4493-800a-bde86ac611ea')
    def test_delete_server_password(self):
        self.client.delete_password(self.server['id'])
