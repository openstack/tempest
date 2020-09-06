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

import testtools

from tempest.api.compute.floating_ips import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class FloatingIPsNegativeTestJSON(base.BaseFloatingIPsTest):
    """Test floating ips API with compute microversion less than 2.36"""

    max_microversion = '2.35'

    @classmethod
    def resource_setup(cls):
        super(FloatingIPsNegativeTestJSON, cls).resource_setup()

        # Generating a nonexistent floatingIP id
        body = cls.client.list_floating_ips()['floating_ips']
        floating_ip_ids = [floating_ip['id'] for floating_ip in body]
        while True:
            if CONF.service_available.neutron:
                cls.non_exist_id = data_utils.rand_uuid()
            else:
                cls.non_exist_id = data_utils.rand_int_id(start=999)
            if cls.non_exist_id not in floating_ip_ids:
                break

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6e0f059b-e4dd-48fb-8207-06e3bba5b074')
    def test_allocate_floating_ip_from_nonexistent_pool(self):
        """Test allocating floating ip from non existent pool should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.create_floating_ip,
                          pool="non_exist_pool")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ae1c55a8-552b-44d4-bfb6-2a115a15d0ba')
    def test_delete_nonexistent_floating_ip(self):
        """Test deleting non existent floating ip should fail"""
        # Deleting the non existent floating IP
        self.assertRaises(lib_exc.NotFound, self.client.delete_floating_ip,
                          self.non_exist_id)


class FloatingIPsAssociationNegativeTestJSON(base.BaseFloatingIPsTest):
    """Test floating ips API with compute microversion less than 2.44"""

    max_microversion = '2.43'

    @classmethod
    def resource_setup(cls):
        super(FloatingIPsAssociationNegativeTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = cls.server['id']

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('595fa616-1a71-4670-9614-46564ac49a4c')
    def test_associate_nonexistent_floating_ip(self):
        """Test associating non existent floating ip to server should fail"""
        # Associating non existent floating IP
        self.assertRaises(lib_exc.NotFound,
                          self.client.associate_floating_ip_to_server,
                          "0.0.0.0", self.server_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0a081a66-e568-4e6b-aa62-9587a876dca8')
    def test_dissociate_nonexistent_floating_ip(self):
        """Test dissociating non existent floating ip should fail"""
        # Dissociating non existent floating IP
        self.assertRaises(lib_exc.NotFound,
                          self.client.disassociate_floating_ip_from_server,
                          "0.0.0.0", self.server_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('804b4fcb-bbf5-412f-925d-896672b61eb3')
    def test_associate_ip_to_server_without_passing_floating_ip(self):
        """Test associating empty floating ip to server should fail"""
        # should raise NotFound or BadRequest(In case of Nova V2.1) exception.
        self.assertRaises((lib_exc.NotFound, lib_exc.BadRequest),
                          self.client.associate_floating_ip_to_server,
                          '', self.server_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('58a80596-ffb2-11e6-9393-fa163e4fa634')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_associate_ip_to_server_with_floating_ip(self):
        """Test associating floating ip to server already with floating ip

        1. The VM have one port
        2. Associate floating IP A to the VM
        3. Associate floating IP B which is from same pool with floating IP A
           to the VM, should raise BadRequest exception
        """
        body = self.client.create_floating_ip(
            pool=CONF.network.public_network_id)['floating_ip']
        self.addCleanup(self.client.delete_floating_ip, body['id'])
        self.client.associate_floating_ip_to_server(body['ip'], self.server_id)
        self.addCleanup(self.client.disassociate_floating_ip_from_server,
                        body['ip'], self.server_id)

        body = self.client.create_floating_ip(
            pool=CONF.network.public_network_id)['floating_ip']
        self.addCleanup(self.client.delete_floating_ip, body['id'])
        self.assertRaises(lib_exc.BadRequest,
                          self.client.associate_floating_ip_to_server,
                          body['ip'], self.server_id)
