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

from tempest.api.compute import base
from tempest import test


class AZAdminV2TestJSON(base.BaseComputeAdminTest):
    """
    Tests Availability Zone API List
    """
    _api_version = 2

    @classmethod
    def setup_clients(cls):
        super(AZAdminV2TestJSON, cls).setup_clients()
        cls.client = cls.availability_zone_admin_client

    @test.attr(type='gate')
    @test.idempotent_id('d3431479-8a09-4f76-aa2d-26dc580cb27c')
    def test_get_availability_zone_list(self):
        # List of availability zone
        availability_zone = self.client.get_availability_zone_list()
        self.assertTrue(len(availability_zone) > 0)

    @test.attr(type='gate')
    @test.idempotent_id('ef726c58-530f-44c2-968c-c7bed22d5b8c')
    def test_get_availability_zone_list_detail(self):
        # List of availability zones and available services
        availability_zone = self.client.get_availability_zone_list_detail()
        self.assertTrue(len(availability_zone) > 0)
