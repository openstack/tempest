# Copyright 2018 NEC Corporation.
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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

# NOTE(gmann): This file is to write the tests which mainly
# tests newly added microversion schema related to servers APIs.
# As per (https://docs.openstack.org/tempest/latest/microversion_testing.
# html#tempest-scope-for-microversion-testing),
# we need to fill the API response schema gaps which gets modified
# during microversion change. To cover the testing of such schema
# we need to have operation schema test which just test
# the microversion schemas.
# If you are adding server APIs microversion schema file without
# their integration tests, you can add tests to cover those schema
# in this file.


class ServerShowV254Test(base.BaseV2ComputeTest):
    min_microversion = '2.54'
    max_microversion = 'latest'

    @decorators.idempotent_id('09170a98-4940-4637-add7-1a35121f1a5a')
    def test_rebuild_server(self):
        server = self.create_test_server(wait_until='ACTIVE')
        keypair_name = data_utils.rand_name(
            self.__class__.__name__ + '-keypair')
        kwargs = {'name': keypair_name}
        self.keypairs_client.create_keypair(**kwargs)
        self.addCleanup(self.keypairs_client.delete_keypair,
                        keypair_name)
        # Checking rebuild API response schema
        self.servers_client.rebuild_server(server['id'], self.image_ref_alt,
                                           key_name=keypair_name)
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')


class ServerShowV257Test(base.BaseV2ComputeTest):
    min_microversion = '2.57'
    max_microversion = 'latest'

    @decorators.idempotent_id('803df848-080a-4261-8f11-b020cd9b6f60')
    def test_rebuild_server(self):
        server = self.create_test_server(wait_until='ACTIVE')
        user_data = "ZWNobyAiaGVsbG8gd29ybGQi"
        # Checking rebuild API response schema
        self.servers_client.rebuild_server(server['id'], self.image_ref_alt,
                                           user_data=user_data)
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')
