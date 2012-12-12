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

from tempest.common.utils.data_utils import arbitrary_string
from tempest.common.utils.data_utils import rand_name
from tempest.tests.object_storage import base


class ContainerTest(base.BaseObjectTest):

    @classmethod
    def setUpClass(cls):
        super(ContainerTest, cls).setUpClass()
        cls.containers = []

    @classmethod
    def tearDownClass(cls):
        for container in cls.containers:
            #Get list of all object in the container
            objlist = \
                cls.container_client.list_all_container_objects(container)

            #Attempt to delete every object in the container
            for obj in objlist:
                resp, _ = \
                    cls.object_client.delete_object(container, obj['name'])

            #Attempt to delete the container
            resp, _ = cls.container_client.delete_container(container)

    @attr(type='smoke')
    def test_create_container(self):
        """Create a container, test responses"""

        #Create a container
        container_name = rand_name(name='TestContainer')
        resp, body = self.container_client.create_container(container_name)
        self.containers.append(container_name)

        self.assertTrue(resp['status'] in ('202', '201'))

    @attr(type='smoke')
    def test_delete_container(self):
        """Create and Delete a container, test responses"""

        #Create a container
        container_name = rand_name(name='TestContainer')
        resp, _ = self.container_client.create_container(container_name)
        self.containers.append(container_name)

        #Delete Container
        resp, _ = self.container_client.delete_container(container_name)
        self.assertEqual(resp['status'], '204')
        self.containers.remove(container_name)

    @attr(type='smoke')
    def test_list_container_contents_json(self):
        """Add metadata to object"""

        #Create a container
        container_name = rand_name(name='TestContainer')
        resp, _ = self.container_client.create_container(container_name)
        self.containers.append(container_name)

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(container_name,
                                                   object_name, data)

        #Set Object Metadata
        meta_key = rand_name(name='Meta-Test-')
        meta_value = rand_name(name='MetaValue-')
        orig_metadata = {meta_key: meta_value}

        resp, _ = self.object_client.update_object_metadata(container_name,
                                                            object_name,
                                                            orig_metadata)

        #Get Container contents list json format
        params = {'format': 'json'}
        resp, object_list = \
            self.container_client.\
            list_container_contents(container_name, params=params)

        self.assertEqual(resp['status'], '200')
        self.assertIsNotNone(object_list)

        object_names = [obj['name'] for obj in object_list]
        self.assertIn(object_name, object_names)

    @attr(type='smoke')
    def test_container_metadata(self):
        """Update/Retrieve/Delete Container Metadata"""

        # Create a container
        container_name = rand_name(name='TestContainer')
        resp, _ = self.container_client.create_container(container_name)
        self.containers.append(container_name)

        # Update container metadata
        metadata = {'name': 'Pictures',
                    'description': 'Travel'
                    }
        resp, _ = \
            self.container_client.update_container_metadata(container_name,
                                                            metadata=metadata)
        self.assertEqual(resp['status'], '204')

        # List container metadata
        resp, _ = self.container_client.list_container_metadata(
                                                            container_name)
        self.assertEqual(resp['status'], '204')
        self.assertIn('x-container-meta-name', resp)
        self.assertIn('x-container-meta-description', resp)
        self.assertEqual(resp['x-container-meta-name'], 'Pictures')
        self.assertEqual(resp['x-container-meta-description'], 'Travel')

        # Delete container metadata
        resp, _ = \
            self.container_client.delete_container_metadata(
                                                    container_name,
                                                    metadata=metadata.keys())
        self.assertEqual(resp['status'], '204')

        resp, _ = self.container_client.list_container_metadata(container_name)
        self.assertEqual(resp['status'], '204')
        self.assertNotIn('x-container-meta-name', resp)
        self.assertNotIn('x-container-meta-description', resp)

        # Delete Container
        resp, _ = self.container_client.delete_container(container_name)
        self.assertEqual(resp['status'], '204')
        self.containers.remove(container_name)
