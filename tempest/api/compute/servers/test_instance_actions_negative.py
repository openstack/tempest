# Copyright 2013 NEC Corporation
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class InstanceActionsNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(InstanceActionsNegativeTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(InstanceActionsNegativeTestJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('67e1fce6-7ec2-45c6-92d4-0a8f1a632910')
    def test_list_instance_actions_non_existent_server(self):
        # List actions of the non-existent server id
        non_existent_server_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.list_instance_actions,
                          non_existent_server_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0269f40a-6f18-456c-b336-c03623c897f1')
    def test_get_instance_action_invalid_request(self):
        # Get the action details of the provided server with invalid request
        self.assertRaises(lib_exc.NotFound, self.client.get_instance_action,
                          self.server_id, '999')
