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
from tempest.tests.compute import base


class FloatingIPDetailsTestBase(object):

    @staticmethod
    def setUpClass(cls):
        cls.client = cls.floating_ips_client
        cls.floating_ip = []
        cls.floating_ip_id = []
        cls.random_number = 0
        for i in range(3):
            resp, body = cls.client.create_floating_ip()
            cls.floating_ip.append(body)
            cls.floating_ip_id.append(body['id'])

    @staticmethod
    def tearDownClass(cls):
        for i in range(3):
            cls.client.delete_floating_ip(cls.floating_ip_id[i])

    @attr(type='positive')
    def test_list_floating_ips(self):
        # Positive test:Should return the list of floating IPs
        resp, body = self.client.list_floating_ips()
        self.assertEqual(200, resp.status)
        floating_ips = body
        self.assertNotEqual(0, len(floating_ips),
                            "Expected floating IPs. Got zero.")
        for i in range(3):
            self.assertTrue(self.floating_ip[i] in floating_ips)

    @attr(type='positive')
    def test_get_floating_ip_details(self):
        # Positive test:Should be able to GET the details of floatingIP
        #Creating a floating IP for which details are to be checked
        try:
            resp, body = self.client.create_floating_ip()
            floating_ip_instance_id = body['instance_id']
            floating_ip_ip = body['ip']
            floating_ip_fixed_ip = body['fixed_ip']
            floating_ip_id = body['id']
            resp, body = \
                self.client.get_floating_ip_details(floating_ip_id)
            self.assertEqual(200, resp.status)
            #Comparing the details of floating IP
            self.assertEqual(floating_ip_instance_id,
                             body['instance_id'])
            self.assertEqual(floating_ip_ip, body['ip'])
            self.assertEqual(floating_ip_fixed_ip,
                             body['fixed_ip'])
            self.assertEqual(floating_ip_id, body['id'])
        #Deleting the floating IP created in this method
        finally:
            self.client.delete_floating_ip(floating_ip_id)

    @attr(type='negative')
    def test_get_nonexistant_floating_ip_details(self):
        # Negative test:Should not be able to GET the details
        # of nonexistant floating IP
        floating_ip_id = []
        resp, body = self.client.list_floating_ips()
        for i in range(len(body)):
            floating_ip_id.append(body[i]['id'])
        #Creating a nonexistant floatingIP id
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in floating_ip_id:
                break
        try:
            resp, body = \
            self.client.get_floating_ip_details(non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to GET the details from a'
                      'nonexistant floating IP')


class FloatingIPDetailsTestJSON(base.BaseComputeTestJSON,
                                FloatingIPDetailsTestBase):
    @classmethod
    def setUpClass(cls):
        super(FloatingIPDetailsTestJSON, cls).setUpClass()
        FloatingIPDetailsTestBase.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        FloatingIPDetailsTestBase.tearDownClass(cls)
        super(FloatingIPDetailsTestJSON, cls).tearDownClass()


class FloatingIPDetailsTestXML(base.BaseComputeTestXML,
                               FloatingIPDetailsTestBase):
    @classmethod
    def setUpClass(cls):
        super(FloatingIPDetailsTestXML, cls).setUpClass()
        FloatingIPDetailsTestBase.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        FloatingIPDetailsTestBase.tearDownClass(cls)
        super(FloatingIPDetailsTestXML, cls).tearDownClass()
