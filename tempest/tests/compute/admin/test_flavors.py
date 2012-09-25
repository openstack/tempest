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

import nose
from nose.plugins.attrib import attr
import unittest2 as unittest

from tempest.tests.compute import base
from tempest.tests import compute


class FlavorsAdminTestBase(object):

    """
    Tests Flavors API Create and Delete that require admin privileges
    """

    @staticmethod
    def setUpClass(cls):
        if not compute.FLAVOR_EXTRA_DATA_ENABLED:
            msg = "FlavorExtraData extension not enabled."
            raise nose.SkipTest(msg)

        cls.client = cls.os.flavors_client
        cls.flavor_name = 'test_flavor'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10
        cls.ephemeral = 10
        cls.new_flavor_id = 1234
        cls.swap = 1024
        cls.rxtx = 1

    @attr(type='positive')
    def test_create_flavor(self):
        """Create a flavor and ensure it is listed
        This operation requires the user to have 'admin' role"""
        #Create the flavor
        resp, flavor = self.client.create_flavor(self.flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 self.ephemeral,
                                                 self.new_flavor_id,
                                                 self.swap, self.rxtx)
        self.assertEqual(200, resp.status)
        self.assertEqual(flavor['name'], self.flavor_name)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(flavor['ram'], self.ram)
        self.assertEqual(int(flavor['id']), self.new_flavor_id)
        self.assertEqual(flavor['swap'], self.swap)
        self.assertEqual(flavor['rxtx_factor'], self.rxtx)
        self.assertEqual(flavor['OS-FLV-EXT-DATA:ephemeral'], self.ephemeral)

        #Verify flavor is retrieved
        resp, flavor = self.client.get_flavor_details(self.new_flavor_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(flavor['name'], self.flavor_name)

        #Delete the flavor
        resp, body = self.client.delete_flavor(flavor['id'])
        self.assertEqual(resp.status, 202)

    @attr(type='positive')
    def test_create_flavor_verify_entry_in_list_details(self):
        """Create a flavor and ensure it's details are listed
        This operation requires the user to have 'admin' role"""
        #Create the flavor
        resp, flavor = self.client.create_flavor(self.flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 self.ephemeral,
                                                 self.new_flavor_id,
                                                 self.swap, self.rxtx)
        flag = False
        #Verify flavor is retrieved
        resp, flavors = self.client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        for flavor in flavors:
            if flavor['name'] == self.flavor_name:
                flag = True
        self.assertTrue(flag)

        #Delete the flavor
        resp, body = self.client.delete_flavor(self.new_flavor_id)
        self.assertEqual(resp.status, 202)

    @attr(type='negative')
    def test_get_flavor_details_for_deleted_flavor(self):
        """Delete a flavor and ensure it is not listed"""
        # Create a test flavor
        resp, flavor = self.client.create_flavor(self.flavor_name,
                                                 self.ram,
                                                 self.vcpus, self.disk,
                                                 self.ephemeral,
                                                 self.new_flavor_id,
                                                 self.swap, self.rxtx)
        self.assertEquals(200, resp.status)

        # Delete the flavor
        resp, _ = self.client.delete_flavor(self.new_flavor_id)
        self.assertEqual(resp.status, 202)

        # Deleted flavors can be seen via detailed GET
        resp, flavor = self.client.get_flavor_details(self.new_flavor_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(flavor['name'], self.flavor_name)

        # Deleted flavors should not show up in a list however
        resp, flavors = self.client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        flag = True
        for flavor in flavors:
            if flavor['name'] == self.flavor_name:
                flag = False
        self.assertTrue(flag)


class FlavorsAdminTestXML(base.BaseComputeAdminTestXML,
                          FlavorsAdminTestBase):

    @classmethod
    def setUpClass(cls):
        super(FlavorsAdminTestXML, cls).setUpClass()
        FlavorsAdminTestBase.setUpClass(cls)


class FlavorsAdminTestJSON(base.BaseComputeAdminTestJSON,
                           FlavorsAdminTestBase):

    @classmethod
    def setUpClass(cls):
        super(FlavorsAdminTestJSON, cls).setUpClass()
        FlavorsAdminTestBase.setUpClass(cls)
