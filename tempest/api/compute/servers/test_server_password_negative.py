# Copyright 2014 Fujitsu Corporation
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
from tempest import config
from tempest import exceptions
from tempest import test


class ServerPasswordNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setUpClass(cls):
        super(ServerPasswordNegativeTestJSON, cls).setUpClass()
        cls.client = cls.servers_client

    @test.attr(type=['negative', 'gate'])
    def test_get_server_password_with_nonexistent_server(self):
        nonexistent_server = data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound,
                          self.client.get_password,
                          nonexistent_server)



class ServerPasswordNegativeTestXML(ServerPasswordNegativeTestJSON):
    _interface = 'xml'
