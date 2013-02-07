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
import testtools

from tempest.common.utils.data_utils import rand_int_id
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.tests import compute
from tempest.tests.compute import base


class FlavorsAdminTestBase(object):

    """
    Tests Flavors API Create and Delete that require admin privileges
    """

    @classmethod
    def setUpClass(self, cls):
        if not compute.FLAVOR_EXTRA_DATA_ENABLED:
            msg = "FlavorExtraData extension not enabled."
            raise cls.skipException(msg)

        cls.client = cls.os.flavors_client
        cls.flavor_name_prefix = 'test_flavor_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10
        cls.ephemeral = 10
        cls.swap = 1024
        cls.rxtx = 2

    @attr(type='positive')
    def test_create_flavor(self):
        # Create a flavor and ensure it is listed
        # This operation requires the user to have 'admin' role
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)

        try:
            #Create the flavor
            resp, flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     ephemeral=self.ephemeral,
                                                     swap=self.swap,
                                                     rxtx=self.rxtx)
            self.assertEqual(200, resp.status)
            self.assertEqual(flavor['name'], flavor_name)
            self.assertEqual(flavor['vcpus'], self.vcpus)
            self.assertEqual(flavor['disk'], self.disk)
            self.assertEqual(flavor['ram'], self.ram)
            self.assertEqual(int(flavor['id']), new_flavor_id)
            self.assertEqual(flavor['swap'], self.swap)
            self.assertEqual(flavor['rxtx_factor'], self.rxtx)
            self.assertEqual(flavor['OS-FLV-EXT-DATA:ephemeral'],
                             self.ephemeral)
            if self._interface == "xml":
                XMLNS_OS_FLV_ACCESS = "http://docs.openstack.org/compute/ext/"\
                    "flavor_access/api/v2"
                key = "{" + XMLNS_OS_FLV_ACCESS + "}is_public"
                self.assertEqual(flavor[key], "True")
            if self._interface == "json":
                self.assertEqual(flavor['os-flavor-access:is_public'], True)

            #Verify flavor is retrieved
            resp, flavor = self.client.get_flavor_details(new_flavor_id)
            self.assertEqual(resp.status, 200)
            self.assertEqual(flavor['name'], flavor_name)

        finally:
            #Delete the flavor
            resp, body = self.client.delete_flavor(new_flavor_id)
            self.assertEqual(resp.status, 202)
            self.client.wait_for_resource_deletion(new_flavor_id)

    @attr(type='positive')
    def test_create_flavor_verify_entry_in_list_details(self):
        # Create a flavor and ensure it's details are listed
        # This operation requires the user to have 'admin' role
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)

        try:
            #Create the flavor
            resp, flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     ephemeral=self.ephemeral,
                                                     swap=self.swap,
                                                     rxtx=self.rxtx)
            flag = False
            #Verify flavor is retrieved
            resp, flavors = self.client.list_flavors_with_detail()
            self.assertEqual(resp.status, 200)
            for flavor in flavors:
                if flavor['name'] == flavor_name:
                    flag = True
            self.assertTrue(flag)

        finally:
            #Delete the flavor
            resp, body = self.client.delete_flavor(new_flavor_id)
            self.assertEqual(resp.status, 202)
            self.client.wait_for_resource_deletion(new_flavor_id)

    @attr(type='negative')
    def test_get_flavor_details_for_deleted_flavor(self):
        # Delete a flavor and ensure it is not listed
        # Create a test flavor
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)

        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram,
                                                 self.vcpus, self.disk,
                                                 new_flavor_id,
                                                 ephemeral=self.ephemeral,
                                                 swap=self.swap,
                                                 rxtx=self.rxtx)
        self.assertEquals(200, resp.status)

        # Delete the flavor
        resp, _ = self.client.delete_flavor(new_flavor_id)
        self.assertEqual(resp.status, 202)

        # Deleted flavors can be seen via detailed GET
        resp, flavor = self.client.get_flavor_details(new_flavor_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(flavor['name'], flavor_name)

        # Deleted flavors should not show up in a list however
        resp, flavors = self.client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        flag = True
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = False
        self.assertTrue(flag)

    def test_create_list_flavor_without_extra_data(self):
        #Create a flavor and ensure it is listed
        #This operation requires the user to have 'admin' role
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)

        try:
            #Create the flavor
            resp, flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id)
            self.assertEqual(200, resp.status)
            self.assertEqual(flavor['name'], flavor_name)
            self.assertEqual(flavor['ram'], self.ram)
            self.assertEqual(flavor['vcpus'], self.vcpus)
            self.assertEqual(flavor['disk'], self.disk)
            self.assertEqual(int(flavor['id']), new_flavor_id)
            self.assertEqual(flavor['swap'], '')
            self.assertEqual(int(flavor['rxtx_factor']), 1)
            self.assertEqual(int(flavor['OS-FLV-EXT-DATA:ephemeral']), 0)
            if self._interface == "xml":
                XMLNS_OS_FLV_ACCESS = "http://docs.openstack.org/compute/ext/"\
                    "flavor_access/api/v2"
                key = "{" + XMLNS_OS_FLV_ACCESS + "}is_public"
                self.assertEqual(flavor[key], "True")
            if self._interface == "json":
                self.assertEqual(flavor['os-flavor-access:is_public'], True)

            #Verify flavor is retrieved
            resp, flavor = self.client.get_flavor_details(new_flavor_id)
            self.assertEqual(resp.status, 200)
            self.assertEqual(flavor['name'], flavor_name)
            #Check if flavor is present in list
            resp, flavors = self.client.list_flavors_with_detail()
            self.assertEqual(resp.status, 200)
            for flavor in flavors:
                if flavor['name'] == flavor_name:
                    flag = True
            self.assertTrue(flag)

        finally:
            #Delete the flavor
            resp, body = self.client.delete_flavor(new_flavor_id)
            self.assertEqual(resp.status, 202)
            self.client.wait_for_resource_deletion(new_flavor_id)

    @attr(type='positive')
    def test_flavor_not_public_verify_entry_not_in_list_details(self):
        #Create a flavor with os-flavor-access:is_public false should not
        #be present in list_details.
        #This operation requires the user to have 'admin' role
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)

        try:
            #Create the flavor
            resp, flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public="False")
            flag = False
            #Verify flavor is retrieved
            resp, flavors = self.client.list_flavors_with_detail()
            self.assertEqual(resp.status, 200)
            for flavor in flavors:
                if flavor['name'] == flavor_name:
                    flag = True
            self.assertFalse(flag)
        finally:
            #Delete the flavor
            resp, body = self.client.delete_flavor(new_flavor_id)
            self.assertEqual(resp.status, 202)

    def test_list_public_flavor_with_other_user(self):
        #Create a Flavor with public access.
        #Try to List/Get flavor with another user
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)

        try:
            #Create the flavor
            resp, flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public="True")
            flag = False
            self.new_client = self.flavors_client
            #Verify flavor is retrieved with new user
            resp, flavors = self.new_client.list_flavors_with_detail()
            self.assertEqual(resp.status, 200)
            for flavor in flavors:
                if flavor['name'] == flavor_name:
                    flag = True
            self.assertTrue(flag)
        finally:
            #Delete the flavor
            resp, body = self.client.delete_flavor(new_flavor_id)
            self.assertEqual(resp.status, 202)
            self.client.wait_for_resource_deletion(new_flavor_id)

    @attr(type='positive')
    def test_is_public_string_variations(self):
        try:
            flavor_id_not_public = rand_int_id(start=1000)
            flavor_name_not_public = rand_name(self.flavor_name_prefix)
            flavor_id_public = rand_int_id(start=1000)
            flavor_name_public = rand_name(self.flavor_name_prefix)

            # Create a non public flavor
            resp, flavor = self.client.create_flavor(flavor_name_not_public,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     flavor_id_not_public,
                                                     is_public="False")

            # Create a public flavor
            resp, flavor = self.client.create_flavor(flavor_name_public,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     flavor_id_public,
                                                     is_public="True")

            def _flavor_lookup(flavors, flavor_name):
                for flavor in flavors:
                    if flavor['name'] == flavor_name:
                        return flavor
                return None

            def _test_string_variations(variations, flavor_name):
                for string in variations:
                    params = {'is_public': string}
                    r, flavors = self.client.list_flavors_with_detail(params)
                    self.assertEqual(r.status, 200)
                    flavor = _flavor_lookup(flavors, flavor_name)
                    self.assertNotEqual(flavor, None)

            _test_string_variations(['f', 'false', 'no', '0'],
                                    flavor_name_not_public)

            _test_string_variations(['t', 'true', 'yes', '1'],
                                    flavor_name_public)

        finally:
            # Delete flavors
            for flavor_id in [flavor_id_not_public, flavor_id_public]:
                resp, body = self.client.delete_flavor(flavor_id)
                self.assertEqual(resp.status, 202)
                self.client.wait_for_resource_deletion(flavor_id)

    @attr(type='negative')
    def test_invalid_is_public_string(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.list_flavors_with_detail,
                          {'is_public': 'invalid'})


class FlavorsAdminTestXML(base.BaseComputeAdminTestXML,
                          base.BaseComputeTestXML,
                          FlavorsAdminTestBase):

    @classmethod
    def setUpClass(cls):
        super(FlavorsAdminTestXML, cls).setUpClass()
        base.BaseComputeTestXML.setUpClass()
        FlavorsAdminTestBase.setUpClass(cls)


class FlavorsAdminTestJSON(base.BaseComputeAdminTestJSON,
                           base.BaseComputeTestJSON,
                           FlavorsAdminTestBase):

    @classmethod
    def setUpClass(cls):
        super(FlavorsAdminTestJSON, cls).setUpClass()
        base.BaseComputeTestJSON.setUpClass()
        FlavorsAdminTestBase.setUpClass(cls)
