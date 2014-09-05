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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class FloatingIPDetailsNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setUpClass(cls):
        super(FloatingIPDetailsNegativeTestJSON, cls).setUpClass()
        cls.client = cls.floating_ips_client

    @test.attr(type=['negative', 'gate'])
    @test.services('network')
    def test_get_nonexistent_floating_ip_details(self):
        # Negative test:Should not be able to GET the details
        # of non-existent floating IP
        # Creating a non-existent floatingIP id
        if CONF.service_available.neutron:
            non_exist_id = str(uuid.uuid4())
        else:
            non_exist_id = data_utils.rand_int_id(start=999)
        self.assertRaises(exceptions.NotFound,
                          self.client.get_floating_ip_details, non_exist_id)

    @test.attr(type=['negative', 'gate'])
    @test.services('network')
    def test_list_floating_ip_with_invalid_pool(self):
        param={'pool' : '11'}
        resp, floating_ip = self.client.list_floating_ips(param)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(floating_ip))

    @test.attr(type=['negative', 'gate'])
    @test.services('network')
    def test_list_floating_ip_pools_with_invalid_pool_name(self):
        param={'nonexist' : 'null'}
        resp, ip_pools = self.client.list_floating_ip_pools(param)
        self.assertEqual(200, resp.status)
        resp, ex_pools = self.client.list_floating_ip_pools()
        self.assertEqual(len(ex_pools), len(ip_pools))

class FloatingIPDetailsNegativeTestXML(FloatingIPDetailsNegativeTestJSON):
    _interface = 'xml'
