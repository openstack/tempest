# Copyright 2012 OpenStack Foundation
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class FloatingIPDetailsNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(FloatingIPDetailsNegativeTestJSON, cls).setup_clients()
        cls.client = cls.floating_ips_client

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('7ab18834-4a4b-4f28-a2c5-440579866695')
    @test.services('network')
    def test_get_nonexistent_floating_ip_details(self):
        # Negative test:Should not be able to GET the details
        # of non-existent floating IP
        # Creating a non-existent floatingIP id
        if CONF.service_available.neutron:
            non_exist_id = str(uuid.uuid4())
        else:
            non_exist_id = data_utils.rand_int_id(start=999)
        self.assertRaises(lib_exc.NotFound,
                          self.client.get_floating_ip_details, non_exist_id)
