# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from nose.plugins.attrib import attr
import unittest2 as unittest

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest import openstack
from tempest.tests.compute import base


class FloatingIPsTestBase(object):
    server_id = None
    floating_ip = None

    @staticmethod
    def setUpClass(cls):
        cls.client = cls.floating_ips_client
        cls.servers_client = cls.servers_client

        #Server creation
        resp, server = cls.servers_client.create_server('floating-server',
                                                        cls.image_ref,
                                                        cls.flavor_ref)
        cls.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        cls.server_id = server['id']
        resp, body = cls.servers_client.get_server(server['id'])
        #Floating IP creation
        resp, body = cls.client.create_floating_ip()
        cls.floating_ip_id = body['id']
        cls.floating_ip = body['ip']
        #Generating a nonexistent floatingIP id
        cls.floating_ip_ids = []
        resp, body = cls.client.list_floating_ips()
        for i in range(len(body)):
            cls.floating_ip_ids.append(body[i]['id'])
        while True:
            cls.non_exist_id = rand_name('999')
            if cls.non_exist_id not in cls.floating_ip_ids:
                break

    @staticmethod
    def tearDownClass(cls):
        #Deleting the server which is created in this method
        resp, body = cls.servers_client.delete_server(cls.server_id)
        #Deleting the floating IP which is created in this method
        resp, body = cls.client.delete_floating_ip(cls.floating_ip_id)

    @attr(type='positive')
    def test_allocate_floating_ip(self):
        """
        Positive test:Allocation of a new floating IP to a project
        should be successful
        """
        try:
            resp, body = self.client.create_floating_ip()
            self.assertEqual(200, resp.status)
            floating_ip_id_allocated = body['id']
            resp, floating_ip_details = \
                self.client.get_floating_ip_details(floating_ip_id_allocated)
            #Checking if the details of allocated IP is in list of floating IP
            resp, body = self.client.list_floating_ips()
            self.assertTrue(floating_ip_details in body)
        finally:
            #Deleting the floating IP which is created in this method
            self.client.delete_floating_ip(floating_ip_id_allocated)

    @attr(type='positive')
    def test_delete_floating_ip(self):
        """
        Positive test:Deletion of valid floating IP from project
        should be successful
        """
        #Creating the floating IP that is to be deleted in this method
        resp, floating_ip_body = self.client.create_floating_ip()
        #Storing the details of floating IP before deleting it
        cli_resp = self.client.get_floating_ip_details(floating_ip_body['id'])
        resp, floating_ip_details = cli_resp
        #Deleting the floating IP from the project
        resp, body = self.client.delete_floating_ip(floating_ip_body['id'])
        self.assertEqual(202, resp.status)
        # Check it was really deleted.
        self.client.wait_for_resource_deletion(floating_ip_body['id'])

    @attr(type='positive')
    def test_associate_disassociate_floating_ip(self):
        """
        Positive test:Associate and disassociate the provided floating IP to a
        specific server should be successful
        """
        #Association of floating IP to fixed IP address
        resp, body =\
        self.client.associate_floating_ip_to_server(self.floating_ip,
                                                    self.server_id)
        self.assertEqual(202, resp.status)
        #Disassociation of floating IP that was associated in this method
        resp, body = \
            self.client.disassociate_floating_ip_from_server(self.floating_ip,
                                                             self.server_id)
        self.assertEqual(202, resp.status)

    @attr(type='negative')
    def test_delete_nonexistant_floating_ip(self):
        """

        Negative test:Deletion of a nonexistent floating IP
        from project should fail
        """
        #Deleting the non existent floating IP
        try:
            resp, body = self.client.delete_floating_ip(self.non_exist_id)
        except:
            pass
        else:
            self.fail('Should not be able to delete a nonexistent floating IP')

    @unittest.skip("Skipped until the Bug #957706 is resolved")
    @attr(type='negative')
    def test_associate_nonexistant_floating_ip(self):
        """
        Negative test:Association of a non existent floating IP
        to specific server should fail
        """
        #Associating non existent floating IP
        try:
            resp, body = \
            self.client.associate_floating_ip_to_server("0.0.0.0",
                                                        self.server_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to associate'
                      ' a nonexistent floating IP')

    @attr(type='negative')
    def test_dissociate_nonexistant_floating_ip(self):
        """
        Negative test:Dissociation of a non existent floating IP should fail
        """
        #Dissociating non existent floating IP
        try:
            resp, body = \
            self.client.disassociate_floating_ip_from_server("0.0.0.0",
                                                             self.server_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to dissociate'
                      ' a nonexistent floating IP')

    @attr(type='positive')
    def test_associate_already_associated_floating_ip(self):
        """
        positive test:Association of an already associated floating IP
        to specific server should change the association of the Floating IP
        """
        #Create server so as to use for Multiple association
        resp, body = self.servers_client.create_server('floating-server2',
                                                       self.image_ref,
                                                       self.flavor_ref)
        self.servers_client.wait_for_server_status(body['id'], 'ACTIVE')
        self.new_server_id = body['id']

        #Associating floating IP for the first time
        resp, _ = \
        self.client.associate_floating_ip_to_server(self.floating_ip,
                                                    self.server_id)
        #Associating floating IP for the second time
        resp, body = \
        self.client.associate_floating_ip_to_server(self.floating_ip,
                                                    self.new_server_id)

        #Make sure no longer associated with old server
        try:
            self.client.disassociate_floating_ip_from_server(
                self.floating_ip,
                self.server_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('The floating IP should be associated to the second '
                      'server')
        if (resp['status'] is not None):
            #Dissociation of the floating IP associated in this method
            resp, _ = \
            self.client.disassociate_floating_ip_from_server(
                self.floating_ip,
                self.new_server_id)
        #Deletion of server created in this method
        resp, body = self.servers_client.delete_server(self.new_server_id)

    @unittest.skip("Skipped until the Bug #957706 is resolved")
    @attr(type='negative')
    def test_associate_ip_to_server_without_passing_floating_ip(self):
        """
        Negative test:Association of empty floating IP to specific server
        should raise NotFound exception
        """
        try:
            resp, body =\
            self.client.associate_floating_ip_to_server('',
                                                        self.server_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Association of floating IP to specific server'
                      ' with out passing floating IP  should raise BadRequest')


class FloatingIPsTestJSON(base.BaseComputeTestJSON, FloatingIPsTestBase):
    @classmethod
    def setUpClass(cls):
        super(FloatingIPsTestJSON, cls).setUpClass()
        FloatingIPsTestBase.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        FloatingIPsTestBase.tearDownClass(cls)
        super(FloatingIPsTestJSON, cls).tearDownClass()


class FloatingIPsTestXML(base.BaseComputeTestXML, FloatingIPsTestBase):
    @classmethod
    def setUpClass(cls):
        super(FloatingIPsTestXML, cls).setUpClass()
        FloatingIPsTestBase.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        FloatingIPsTestBase.tearDownClass(cls)
        super(FloatingIPsTestXML, cls).tearDownClass()
