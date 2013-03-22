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

from tempest.common.utils.data_utils import arbitrary_string
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr
from tempest.tests.object_storage import base
import testtools
from time import sleep


class ObjectExpiryTest(base.BaseObjectTest):

    @classmethod
    def setUpClass(cls):
        super(ObjectExpiryTest, cls).setUpClass()

        #Create a container
        cls.container_name = rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)

    @classmethod
    def tearDownClass(cls):
        """The test script fails in tear down class
        as the container contains expired objects (LP bug 1069849).
        But delete action for the expired object is raising
        NotFound exception and also non empty container cannot be deleted.
        """

        #Get list of all object in the container
        objlist = \
            cls.container_client.list_all_container_objects(cls.container_name)

        #Attempt to delete every object in the container
        if objlist:
            for obj in objlist:
                resp, _ = cls.object_client.delete_object(cls.container_name,
                                                          obj['name'])

        #Attempt to delete the container
        resp, _ = cls.container_client.delete_container(cls.container_name)

    @testtools.skip('Until Bug #1069849 is resolved.')
    @attr(type='regression')
    def test_get_object_after_expiry_time(self):
        # GET object after expiry time
        #TODO(harika-vakadi): Similar test case has to be created for
        # "X-Delete-At", after this test case works.

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        #Update object metadata with expiry time of 3 seconds
        metadata = {'X-Delete-After': '3'}
        resp, _ = \
            self.object_client.update_object_metadata(self.container_name,
                                                      object_name, metadata,
                                                      metadata_prefix='')

        resp, _ = \
            self.object_client.list_object_metadata(self.container_name,
                                                    object_name)

        self.assertEqual(resp['status'], '200')
        self.assertIn('x-delete-at', resp)

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertEqual(resp['status'], '200')
        # Check data
        self.assertEqual(body, data)
        # Sleep for over 5 seconds, so that object is expired
        sleep(5)
        # Verification of raised exception after object gets expired
        self.assertRaises(exceptions.NotFound, self.object_client.get_object,
                          self.container_name, object_name)
