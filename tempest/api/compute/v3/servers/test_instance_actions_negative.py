# Copyright 2014 NEC Corporation
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
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class InstanceActionsNegativeV3Test(base.BaseV3ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(InstanceActionsNegativeV3Test, cls).setUpClass()
        cls.client = cls.servers_client
        resp, server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

    @test.attr(type=['negative', 'gate'])
    def test_list_instance_actions_invalid_server(self):
        # List actions of the invalid server id
        invalid_server_id = data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound,
                          self.client.list_instance_actions, invalid_server_id)

    @test.attr(type=['negative', 'gate'])
    def test_get_instance_action_invalid_request(self):
        # Get the action details of the provided server with invalid request
        invalid_request_id = 'req-' + data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound, self.client.get_instance_action,
                          self.server_id, invalid_request_id)
