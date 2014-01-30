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

from tempest.api.compute.floating_ips import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.test import attr

CONF = config.CONF


class FloatingIPsNegativeTestJSON(base.BaseFloatingIPsTest):
    _interface = 'json'
    server_id = None

    @classmethod
    def setUpClass(cls):
        super(FloatingIPsNegativeTestJSON, cls).setUpClass()
        cls.client = cls.floating_ips_client

        # Server creation
        resp, server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']
        # Generating a nonexistent floatingIP id
        cls.floating_ip_ids = []
        resp, body = cls.client.list_floating_ips()
        for i in range(len(body)):
            cls.floating_ip_ids.append(body[i]['id'])
        while True:
            cls.non_exist_id = data_utils.rand_int_id(start=999)
            if CONF.service_available.neutron:
                cls.non_exist_id = str(uuid.uuid4())
            if cls.non_exist_id not in cls.floating_ip_ids:
                break

    @attr(type=['negative', 'gate'])
    def test_allocate_floating_ip_from_nonexistent_pool(self):
        # Negative test:Allocation of a new floating IP from a nonexistent_pool
        # to a project should fail
        self.assertRaises(exceptions.NotFound,
                          self.client.create_floating_ip,
                          "non_exist_pool")

    @attr(type=['negative', 'gate'])
    def test_delete_nonexistent_floating_ip(self):
        # Negative test:Deletion of a nonexistent floating IP
        # from project should fail

        # Deleting the non existent floating IP
        self.assertRaises(exceptions.NotFound, self.client.delete_floating_ip,
                          self.non_exist_id)

    @attr(type=['negative', 'gate'])
    def test_associate_nonexistent_floating_ip(self):
        # Negative test:Association of a non existent floating IP
        # to specific server should fail
        # Associating non existent floating IP
        self.assertRaises(exceptions.NotFound,
                          self.client.associate_floating_ip_to_server,
                          "0.0.0.0", self.server_id)

    @attr(type=['negative', 'gate'])
    def test_dissociate_nonexistent_floating_ip(self):
        # Negative test:Dissociation of a non existent floating IP should fail
        # Dissociating non existent floating IP
        self.assertRaises(exceptions.NotFound,
                          self.client.disassociate_floating_ip_from_server,
                          "0.0.0.0", self.server_id)

    @attr(type=['negative', 'gate'])
    def test_associate_ip_to_server_without_passing_floating_ip(self):
        # Negative test:Association of empty floating IP to specific server
        # should raise NotFound exception
        self.assertRaises(exceptions.NotFound,
                          self.client.associate_floating_ip_to_server,
                          '', self.server_id)


class FloatingIPsNegativeTestXML(FloatingIPsNegativeTestJSON):
    _interface = 'xml'
