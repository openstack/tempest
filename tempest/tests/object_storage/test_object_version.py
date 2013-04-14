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

from tempest.common.utils.data_utils import rand_name
from tempest.test import attr
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

    def assertContainer(self, container, count, byte, versioned):
        resp, _ = self.container_client.list_container_metadata(container)
        self.assertEqual(resp['status'], ('204'))
        header_value = resp.get('x-container-object-count', 'Missing Header')
        self.assertEqual(header_value, count)
        header_value = resp.get('x-container-bytes-used', 'Missing Header')
        self.assertEqual(header_value, byte)
        header_value = resp.get('x-versions-location', 'Missing Header')
        self.assertEqual(header_value, versioned)

    @attr(type='smoke')
    def test_versioned_container(self):
        # Versioned container responses tests

        # Create a containers
        vers_container_name = rand_name(name='TestVersionContainer')
        resp, body = self.container_client.create_container(
            vers_container_name)
        self.containers.append(vers_container_name)
        self.assertIn(resp['status'], ('202', '201'))
        self.assertContainer(vers_container_name, '0', '0',
                             'Missing Header')

        base_container_name = rand_name(name='TestBaseContainer')
        headers = {'X-versions-Location': vers_container_name}
        resp, body = self.container_client.create_container(
            base_container_name,
            metadata=headers,
            metadata_prefix='')
        self.containers.append(base_container_name)
        self.assertIn(resp['status'], ('202', '201'))
        self.assertContainer(base_container_name, '0', '0',
                             vers_container_name)
        # Create Object
        object_name = rand_name(name='TestObject')
        resp, _ = self.object_client.create_object(base_container_name,
                                                   object_name, '1')

        resp, _ = self.object_client.create_object(base_container_name,
                                                   object_name, '2')

        resp, body = self.object_client.get_object(base_container_name,
                                                   object_name)
        self.assertEqual(body, '2')
        # Delete Object version 2
        resp, _ = self.object_client.delete_object(base_container_name,
                                                   object_name)
        self.assertContainer(base_container_name, '1', '1',
                             vers_container_name)
        resp, body = self.object_client.get_object(base_container_name,
                                                   object_name)
        self.assertEqual(body, '1')

        # Delete Object version 1
        resp, _ = self.object_client.delete_object(base_container_name,
                                                   object_name)
        # Containers are Empty
        self.assertContainer(base_container_name, '0', '0',
                             vers_container_name)
        self.assertContainer(vers_container_name, '0', '0',
                             'Missing Header')

        # Delete Containers
        resp, _ = self.container_client.delete_container(base_container_name)
        self.assertEqual(resp['status'], '204')
        self.containers.remove(base_container_name)

        resp, _ = self.container_client.delete_container(vers_container_name)
        self.assertEqual(resp['status'], '204')
        self.containers.remove(vers_container_name)
