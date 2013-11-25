# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.api.object_storage import base
from tempest.common.utils import data_utils
from tempest.test import attr
from tempest.test import HTTP_SUCCESS


class ContainerTest(base.BaseObjectTest):
    @classmethod
    def setUpClass(cls):
        super(ContainerTest, cls).setUpClass()
        cls.containers = []

    @classmethod
    def tearDownClass(cls):
        cls.delete_containers(cls.containers)
        super(ContainerTest, cls).tearDownClass()

    @attr(type='smoke')
    def test_create_container(self):
        container_name = data_utils.rand_name(name='TestContainer')
        resp, body = self.container_client.create_container(container_name)
        self.containers.append(container_name)
        self.assertIn(resp['status'], ('202', '201'))

    @attr(type='smoke')
    def test_delete_container(self):
        # create a container
        container_name = data_utils.rand_name(name='TestContainer')
        resp, _ = self.container_client.create_container(container_name)
        self.containers.append(container_name)
        # delete container
        resp, _ = self.container_client.delete_container(container_name)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.containers.remove(container_name)

    @attr(type='smoke')
    def test_list_container_contents_json(self):
        # add metadata to an object

        # create a container
        container_name = data_utils.rand_name(name='TestContainer')
        resp, _ = self.container_client.create_container(container_name)
        self.containers.append(container_name)
        # create object
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        resp, _ = self.object_client.create_object(container_name,
                                                   object_name, data)
        # set object metadata
        meta_key = data_utils.rand_name(name='Meta-Test-')
        meta_value = data_utils.rand_name(name='MetaValue-')
        orig_metadata = {meta_key: meta_value}
        resp, _ = self.object_client.update_object_metadata(container_name,
                                                            object_name,
                                                            orig_metadata)
        # get container contents list
        params = {'format': 'json'}
        resp, object_list = \
            self.container_client.\
            list_container_contents(container_name, params=params)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.assertIsNotNone(object_list)

        object_names = [obj['name'] for obj in object_list]
        self.assertIn(object_name, object_names)

    @attr(type='smoke')
    def test_container_metadata(self):
        # update/retrieve/delete container metadata

        # create a container
        container_name = data_utils.rand_name(name='TestContainer')
        resp, _ = self.container_client.create_container(container_name)
        self.containers.append(container_name)
        # update container metadata
        metadata = {'name': 'Pictures',
                    'description': 'Travel'
                    }
        resp, _ = \
            self.container_client.update_container_metadata(container_name,
                                                            metadata=metadata)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)

        # list container metadata
        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.assertIn('x-container-meta-name', resp)
        self.assertIn('x-container-meta-description', resp)
        self.assertEqual(resp['x-container-meta-name'], 'Pictures')
        self.assertEqual(resp['x-container-meta-description'], 'Travel')

        # delete container metadata
        resp, _ = self.container_client.delete_container_metadata(
            container_name,
            metadata=metadata.keys())
        self.assertIn(int(resp['status']), HTTP_SUCCESS)

        # check if the metadata are no longer there
        resp, _ = self.container_client.list_container_metadata(container_name)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.assertNotIn('x-container-meta-name', resp)
        self.assertNotIn('x-container-meta-description', resp)
