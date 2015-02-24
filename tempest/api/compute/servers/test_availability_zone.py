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
from tempest import test


class AZV2TestJSON(base.BaseComputeTest):
    """
    Tests Availability Zone API List
    """
    _api_version = 2

    @classmethod
    def setup_clients(cls):
        super(AZV2TestJSON, cls).setup_clients()
        cls.client = cls.availability_zone_client

    @test.attr(type='gate')
    @test.idempotent_id('a8333aa2-205c-449f-a828-d38c2489bf25')
    def test_get_availability_zone_list_with_non_admin_user(self):
        # List of availability zone with non-administrator user
        availability_zone = self.client.get_availability_zone_list()
        self.assertTrue(len(availability_zone) > 0)
