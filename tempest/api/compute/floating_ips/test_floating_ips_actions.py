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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute.floating_ips import base
from tempest import test


class FloatingIPsTestJSON(base.BaseFloatingIPsTest):
    server_id = None
    floating_ip = None

    @classmethod
    def setup_clients(cls):
        super(FloatingIPsTestJSON, cls).setup_clients()
        cls.client = cls.floating_ips_client

    @classmethod
    def resource_setup(cls):
        super(FloatingIPsTestJSON, cls).resource_setup()
        cls.floating_ip_id = None

        # Server creation
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']
        # Floating IP creation
        body = cls.client.create_floating_ip()
        cls.floating_ip_id = body['id']
        cls.floating_ip = body['ip']

    @classmethod
    def resource_cleanup(cls):
        # Deleting the floating IP which is created in this method
        if cls.floating_ip_id:
            cls.client.delete_floating_ip(cls.floating_ip_id)
        super(FloatingIPsTestJSON, cls).resource_cleanup()

    def _try_delete_floating_ip(self, floating_ip_id):
        # delete floating ip, if it exists
        try:
            self.client.delete_floating_ip(floating_ip_id)
        # if not found, it depicts it was deleted in the test
        except lib_exc.NotFound:
            pass

    @test.attr(type='gate')
    @test.idempotent_id('f7bfb946-297e-41b8-9e8c-aba8e9bb5194')
    @test.services('network')
    def test_allocate_floating_ip(self):
        # Positive test:Allocation of a new floating IP to a project
        # should be successful
        body = self.client.create_floating_ip()
        floating_ip_id_allocated = body['id']
        self.addCleanup(self.client.delete_floating_ip,
                        floating_ip_id_allocated)
        floating_ip_details = \
            self.client.get_floating_ip_details(floating_ip_id_allocated)
        # Checking if the details of allocated IP is in list of floating IP
        body = self.client.list_floating_ips()
        self.assertIn(floating_ip_details, body)

    @test.attr(type='gate')
    @test.idempotent_id('de45e989-b5ca-4a9b-916b-04a52e7bbb8b')
    @test.services('network')
    def test_delete_floating_ip(self):
        # Positive test:Deletion of valid floating IP from project
        # should be successful
        # Creating the floating IP that is to be deleted in this method
        floating_ip_body = self.client.create_floating_ip()
        self.addCleanup(self._try_delete_floating_ip, floating_ip_body['id'])
        # Deleting the floating IP from the project
        self.client.delete_floating_ip(floating_ip_body['id'])
        # Check it was really deleted.
        self.client.wait_for_resource_deletion(floating_ip_body['id'])

    @test.attr(type='gate')
    @test.idempotent_id('307efa27-dc6f-48a0-8cd2-162ce3ef0b52')
    @test.services('network')
    def test_associate_disassociate_floating_ip(self):
        # Positive test:Associate and disassociate the provided floating IP
        # to a specific server should be successful

        # Association of floating IP to fixed IP address
        self.client.associate_floating_ip_to_server(
            self.floating_ip,
            self.server_id)

        # Check instance_id in the floating_ip body
        body = self.client.get_floating_ip_details(self.floating_ip_id)
        self.assertEqual(self.server_id, body['instance_id'])

        # Disassociation of floating IP that was associated in this method
        self.client.disassociate_floating_ip_from_server(
            self.floating_ip,
            self.server_id)

    @test.attr(type='gate')
    @test.idempotent_id('6edef4b2-aaf1-4abc-bbe3-993e2561e0fe')
    @test.services('network')
    def test_associate_already_associated_floating_ip(self):
        # positive test:Association of an already associated floating IP
        # to specific server should change the association of the Floating IP
        # Create server so as to use for Multiple association
        new_name = data_utils.rand_name('floating_server')
        body = self.create_test_server(name=new_name)
        self.servers_client.wait_for_server_status(body['id'], 'ACTIVE')
        self.new_server_id = body['id']
        self.addCleanup(self.servers_client.delete_server, self.new_server_id)

        # Associating floating IP for the first time
        self.client.associate_floating_ip_to_server(
            self.floating_ip,
            self.server_id)
        # Associating floating IP for the second time
        self.client.associate_floating_ip_to_server(
            self.floating_ip,
            self.new_server_id)

        self.addCleanup(self.client.disassociate_floating_ip_from_server,
                        self.floating_ip,
                        self.new_server_id)

        # Make sure no longer associated with old server
        self.assertRaises((lib_exc.NotFound,
                           lib_exc.UnprocessableEntity,
                           lib_exc.Conflict),
                          self.client.disassociate_floating_ip_from_server,
                          self.floating_ip, self.server_id)
