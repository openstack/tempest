# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
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

import uuid

from tempest.api.compute import base
from tempest import exceptions
from tempest import test


class VirtualInterfacesNegativeTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        # For this test no network resources are needed
        cls.set_network_resources()
        super(VirtualInterfacesNegativeTestJSON, cls).setUpClass()
        cls.client = cls.servers_client

    @test.attr(type=['negative', 'gate'])
    def test_list_virtual_interfaces_invalid_server_id(self):
        # Negative test: Should not be able to GET virtual interfaces
        # for an invalid server_id
        invalid_server_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound,
                          self.client.list_virtual_interfaces,
                          invalid_server_id)


class VirtualInterfacesNegativeTestXML(VirtualInterfacesNegativeTestJSON):
    _interface = 'xml'
