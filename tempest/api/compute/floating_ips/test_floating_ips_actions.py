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

from tempest.api.compute.floating_ips import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class FloatingIPsTestJSON(base.BaseFloatingIPsTest):
    server_id = None
    floating_ip = None

    @classmethod
    def setUpClass(cls):
        super(FloatingIPsTestJSON, cls).setUpClass()
        cls.client = cls.floating_ips_client
        #cls.servers_client = cls.servers_client

        # Server creation
        resp, server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']
        # Floating IP creation
        resp, body = cls.client.create_floating_ip()
        cls.floating_ip_id = body['id']
        cls.floating_ip = body['ip']

    @classmethod
    def tearDownClass(cls):
        # Deleting the floating IP which is created in this method
        resp, body = cls.client.delete_floating_ip(cls.floating_ip_id)
        super(FloatingIPsTestJSON, cls).tearDownClass()

    @test.attr(type='gate')
    def test_allocate_floating_ip(self):
        # Positive test:Allocation of a new floating IP to a project
        # should be successful
        resp, body = self.client.create_floating_ip()
        floating_ip_id_allocated = body['id']
        self.addCleanup(self.client.delete_floating_ip,
                        floating_ip_id_allocated)
        self.assertEqual(200, resp.status)
        resp, floating_ip_details = \
            self.client.get_floating_ip_details(floating_ip_id_allocated)
        # Checking if the details of allocated IP is in list of floating IP
        resp, body = self.client.list_floating_ips()
        self.assertIn(floating_ip_details, body)

    @test.attr(type='gate')
    def test_delete_floating_ip(self):
        # Positive test:Deletion of valid floating IP from project
        # should be successful
        # Creating the floating IP that is to be deleted in this method
        resp, floating_ip_body = self.client.create_floating_ip()
        # Storing the details of floating IP before deleting it
        cli_resp = self.client.get_floating_ip_details(floating_ip_body['id'])
        resp, floating_ip_details = cli_resp
        # Deleting the floating IP from the project
        resp, body = self.client.delete_floating_ip(floating_ip_body['id'])
        self.assertEqual(202, resp.status)
        # Check it was really deleted.
        self.client.wait_for_resource_deletion(floating_ip_body['id'])

    @test.attr(type='gate')
    def test_associate_disassociate_floating_ip(self):
        # Positive test:Associate and disassociate the provided floating IP
        # to a specific server should be successful

        # Association of floating IP to fixed IP address
        resp, body = self.client.associate_floating_ip_to_server(
            self.floating_ip,
            self.server_id)
        self.assertEqual(202, resp.status)
        # Disassociation of floating IP that was associated in this method
        resp, body = self.client.disassociate_floating_ip_from_server(
            self.floating_ip,
            self.server_id)
        self.assertEqual(202, resp.status)

    @test.attr(type='gate')
    def test_associate_already_associated_floating_ip(self):
        # positive test:Association of an already associated floating IP
        # to specific server should change the association of the Floating IP
        # Create server so as to use for Multiple association
        new_name = data_utils.rand_name('floating_server')
        resp, body = self.create_test_server(name=new_name)
        self.servers_client.wait_for_server_status(body['id'], 'ACTIVE')
        self.new_server_id = body['id']

        # Associating floating IP for the first time
        resp, _ = self.client.associate_floating_ip_to_server(
            self.floating_ip,
            self.server_id)
        # Associating floating IP for the second time
        resp, body = self.client.associate_floating_ip_to_server(
            self.floating_ip,
            self.new_server_id)

        self.addCleanup(self.servers_client.delete_server, self.new_server_id)
        if (resp['status'] is not None):
            self.addCleanup(self.client.disassociate_floating_ip_from_server,
                            self.floating_ip,
                            self.new_server_id)

        # Make sure no longer associated with old server
        self.assertRaises((exceptions.NotFound,
                           exceptions.UnprocessableEntity),
                          self.client.disassociate_floating_ip_from_server,
                          self.floating_ip, self.server_id)


class FloatingIPsTestXML(FloatingIPsTestJSON):
    _interface = 'xml'
