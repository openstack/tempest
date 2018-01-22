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

from tempest.api.compute import base
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class VirtualInterfacesNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_credentials(cls):
        # For this test no network resources are needed
        cls.set_network_resources()
        super(VirtualInterfacesNegativeTestJSON, cls).setup_credentials()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('64ebd03c-1089-4306-93fa-60f5eb5c803c')
    @utils.services('network')
    def test_list_virtual_interfaces_invalid_server_id(self):
        # Negative test: Should not be able to GET virtual interfaces
        # for an invalid server_id
        invalid_server_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.servers_client.list_virtual_interfaces,
                          invalid_server_id)
