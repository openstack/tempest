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

import re
import unittest2 as unittest
import tempest.config

from nose.plugins.attrib import attr
from tempest import exceptions
from tempest import openstack
from tempest.common.utils.data_utils import rand_name, arbitrary_string
from tempest.tests.object_storage import base


class ObjectTest(base.BaseObjectTest):

    @classmethod
    def setUpClass(cls):
        super(ObjectTest, cls).setUpClass()

        #Create a container
        cls.container_name = rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)

    @classmethod
    def tearDownClass(cls):
        #Get list of all object in the container
        objlist = \
            cls.container_client.list_all_container_objects(cls.container_name)

        #Attempt to delete every object in the container
        for obj in objlist:
            resp, _ = cls.object_client.delete_object(cls.container_name,
                                                      obj['name'])

        #Attempt to delete the container
        resp, _ = cls.container_client.delete_container(cls.container_name)

    @attr(type='smoke')
    def test_create_object(self):
        """Create storage object, test response"""

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        #Create another Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertEqual(resp['status'], '201')

    @attr(type='smoke')
    def test_delete_object(self):
        """Create and delete a storage object, test responses"""

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        resp, _ = self.object_client.delete_object(self.container_name,
                                                   object_name)
        self.assertEqual(resp['status'], '204')

    @attr(type='smoke')
    def test_object_metadata(self):
        """Add metadata to storage object, test if metadata is retrievable"""

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        #Set Object Metadata
        meta_key = rand_name(name='test-')
        meta_value = rand_name(name='MetaValue-')
        orig_metadata = {meta_key: meta_value}

        resp, _ = \
            self.object_client.update_object_metadata(self.container_name,
                                                      object_name,
                                                      orig_metadata)
        self.assertEqual(resp['status'], '202')

        #Get Object Metadata
        resp, resp_metadata = \
            self.object_client.list_object_metadata(self.container_name,
                                                    object_name)
        self.assertEqual(resp['status'], '200')
        actual_meta_key = 'x-object-meta-' + meta_key
        self.assertTrue(actual_meta_key in resp)
        self.assertEqual(resp[actual_meta_key], meta_value)
