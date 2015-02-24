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

from tempest.api.compute.floating_ips import base
from tempest import config
from tempest import test

CONF = config.CONF


class FloatingIPsNegativeTestJSON(base.BaseFloatingIPsTest):
    server_id = None

    @classmethod
    def setup_clients(cls):
        super(FloatingIPsNegativeTestJSON, cls).setup_clients()
        cls.client = cls.floating_ips_client

    @classmethod
    def resource_setup(cls):
        super(FloatingIPsNegativeTestJSON, cls).resource_setup()

        # Server creation
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']
        # Generating a nonexistent floatingIP id
        cls.floating_ip_ids = []
        body = cls.client.list_floating_ips()
        for i in range(len(body)):
            cls.floating_ip_ids.append(body[i]['id'])
        while True:
            cls.non_exist_id = data_utils.rand_int_id(start=999)
            if CONF.service_available.neutron:
                cls.non_exist_id = str(uuid.uuid4())
            if cls.non_exist_id not in cls.floating_ip_ids:
                break

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('6e0f059b-e4dd-48fb-8207-06e3bba5b074')
    @test.services('network')
    def test_allocate_floating_ip_from_nonexistent_pool(self):
        # Negative test:Allocation of a new floating IP from a nonexistent_pool
        # to a project should fail
        self.assertRaises(lib_exc.NotFound,
                          self.client.create_floating_ip,
                          "non_exist_pool")

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ae1c55a8-552b-44d4-bfb6-2a115a15d0ba')
    @test.services('network')
    def test_delete_nonexistent_floating_ip(self):
        # Negative test:Deletion of a nonexistent floating IP
        # from project should fail

        # Deleting the non existent floating IP
        self.assertRaises(lib_exc.NotFound, self.client.delete_floating_ip,
                          self.non_exist_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('595fa616-1a71-4670-9614-46564ac49a4c')
    @test.services('network')
    def test_associate_nonexistent_floating_ip(self):
        # Negative test:Association of a non existent floating IP
        # to specific server should fail
        # Associating non existent floating IP
        self.assertRaises(lib_exc.NotFound,
                          self.client.associate_floating_ip_to_server,
                          "0.0.0.0", self.server_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0a081a66-e568-4e6b-aa62-9587a876dca8')
    @test.services('network')
    def test_dissociate_nonexistent_floating_ip(self):
        # Negative test:Dissociation of a non existent floating IP should fail
        # Dissociating non existent floating IP
        self.assertRaises(lib_exc.NotFound,
                          self.client.disassociate_floating_ip_from_server,
                          "0.0.0.0", self.server_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('804b4fcb-bbf5-412f-925d-896672b61eb3')
    @test.services('network')
    def test_associate_ip_to_server_without_passing_floating_ip(self):
        # Negative test:Association of empty floating IP to specific server
        # should raise NotFound or BadRequest(In case of Nova V2.1) exception.
        self.assertRaises((lib_exc.NotFound, lib_exc.BadRequest),
                          self.client.associate_floating_ip_to_server,
                          '', self.server_id)
