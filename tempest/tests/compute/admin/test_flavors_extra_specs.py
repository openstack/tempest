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

from tempest import exceptions
from tempest.tests import compute
from tempest.tests.compute import base
import testtools


class FlavorsExtraSpecsTestBase(object):

    """
    Tests Flavor Extra Spec API extension.
    SET, UNSET Flavor Extra specs require admin privileges.
    GET Flavor Extra specs can be performed even by without admin privileges.
    """

    @classmethod
    def setUpClass(self, cls):
        if not compute.FLAVOR_EXTRA_DATA_ENABLED:
            msg = "FlavorExtraData extension not enabled."
            raise cls.skipException(msg)

        cls.client = cls.os.flavors_client
        flavor_name = 'test_flavor2'
        ram = 512
        vcpus = 1
        disk = 10
        ephemeral = 10
        cls.new_flavor_id = 12345
        swap = 1024
        rxtx = 1
        #Create a flavor so as to set/get/unset extra specs
        resp, cls.flavor = cls.client.create_flavor(flavor_name,
                                                    ram, vcpus,
                                                    disk,
                                                    cls.new_flavor_id,
                                                    ephemeral=ephemeral,
                                                    swap=swap, rxtx=rxtx)

    @classmethod
    def tearDownClass(self, cls):
        resp, body = cls.client.delete_flavor(cls.flavor['id'])

    def test_flavor_set_get_unset_keys(self):
        #Test to SET, GET UNSET flavor extra spec as a user
        #with admin privileges.
        #Assigning extra specs values that are to be set
        specs = {"key1": "value1", "key2": "value2"}
        #SET extra specs to the flavor created in setUp
        set_resp, set_body = \
            self.client.set_flavor_extra_spec(self.flavor['id'], specs)
        self.assertEqual(set_resp.status, 200)
        self.assertEqual(set_body, specs)
        #GET extra specs and verify
        get_resp, get_body = \
            self.client.get_flavor_extra_spec(self.flavor['id'])
        self.assertEqual(get_resp.status, 200)
        self.assertEqual(get_body, specs)
        #UNSET extra specs that were set in this test
        unset_resp, _ = \
            self.client.unset_flavor_extra_spec(self.flavor['id'], "key1")
        self.assertEqual(unset_resp.status, 200)

    @testtools.skip('Until bug 1094142 is resolved.')
    def test_flavor_non_admin_set_get_unset_keys(self):
        #Test to SET, GET UNSET flavor extra spec as a user
        #with out admin privileges.
        self.nonadmin_client = self.flavors_client
        #Assigning extra specs values that are to be set
        specs = {"key1": "value1", "key2": "value2"}
        msg = None

        #Verify if able to SET flavor extraspec with non-admin user
        try:
            set_resp, set_body = \
                self.nonadmin_client.set_flavor_extra_spec(
                    self.flavor['id'], specs)
        except exceptions.Unauthorized:
            pass
        else:
            msg = "Flavor extra specs is being SET"
            msg += " by unauthorized non-admin user.\n"
        #SET flavor extra specs with admin user
        #so as to check GET/UNSET flavor extra specs with non-admin
        set_resp, set_body =\
            self.client.set_flavor_extra_spec(self.flavor['id'], specs)
        #Verify if able to GET flavor extraspec with non-admin user
        try:
            get_resp, get_body = \
                self.nonadmin_client.get_flavor_extra_spec('')
            self.assertEqual(get_resp.status, 200)
        except Exception as e:
            msg += "Got an exception when GET Flavor extra specs"
            msg += " by non-admin user. Exception is: %s\n" % e
        #Verify if able to UNSET flavor extraspec with non-admin user
        try:
            unset_resp, _ = \
                self.nonadmin_client.unset_flavor_extra_spec(self.flavor['id'],
                                                             "key1")
        except exceptions.Unauthorized:
            pass
        else:
            msg += "Flavor extra specs is being UNSET"
            msg += " by unauthorized non-admin user.\n"
        #Verification to check if actions failed.
        #msg variable  would contain the message according to the failures.
        if msg is not None:
            self.fail(msg)


class FlavorsExtraSpecsTestXML(base.BaseComputeAdminTestXML,
                               base.BaseComputeTestXML,
                               FlavorsExtraSpecsTestBase):

    @classmethod
    def setUpClass(cls):
        super(FlavorsExtraSpecsTestXML, cls).setUpClass()
        base.BaseComputeTestXML.setUpClass()
        FlavorsExtraSpecsTestBase.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        FlavorsExtraSpecsTestBase.tearDownClass(cls)
        super(FlavorsExtraSpecsTestXML, cls).tearDownClass()


class FlavorsExtraSpecsTestJSON(base.BaseComputeAdminTestJSON,
                                base.BaseComputeTestJSON,
                                FlavorsExtraSpecsTestBase):

    @classmethod
    def setUpClass(cls):
        super(FlavorsExtraSpecsTestJSON, cls).setUpClass()
        base.BaseComputeTestJSON.setUpClass()
        FlavorsExtraSpecsTestBase.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        FlavorsExtraSpecsTestBase.tearDownClass(cls)
        super(FlavorsExtraSpecsTestJSON, cls).tearDownClass()
