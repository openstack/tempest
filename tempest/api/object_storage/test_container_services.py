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
from tempest import test


class ContainerTest(base.BaseObjectTest):
    def setUp(self):
        super(ContainerTest, self).setUp()
        self.containers = []

    def tearDown(self):
        self.delete_containers(self.containers)
        super(ContainerTest, self).tearDown()

    def _create_container(self):
        # setup container
        container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.create_container(container_name)
        self.containers.append(container_name)

        return container_name

    def _create_object(self, container_name, object_name=None):
        # setup object
        if object_name is None:
            object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        self.object_client.create_object(container_name,
                                         object_name,
                                         data)

        return object_name

    @test.attr(type='smoke')
    def test_create_container(self):
        container_name = data_utils.rand_name(name='TestContainer')
        resp, body = self.container_client.create_container(container_name)
        self.containers.append(container_name)
        self.assertIn(resp['status'], ('202', '201'))
        self.assertHeaders(resp, 'Container', 'PUT')

    @test.attr(type='smoke')
    def test_create_container_overwrite(self):
        # overwrite container with the same name
        container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.create_container(container_name)
        self.containers.append(container_name)

        resp, _ = self.container_client.create_container(container_name)
        self.assertIn(resp['status'], ('202', '201'))
        self.assertHeaders(resp, 'Container', 'PUT')

    @test.attr(type='smoke')
    def test_create_container_with_metadata_key(self):
        # create container with the blank value of metadata
        container_name = data_utils.rand_name(name='TestContainer')
        metadata = {'test-container-meta': ''}
        resp, _ = self.container_client.create_container(
            container_name,
            metadata=metadata)
        self.containers.append(container_name)
        self.assertIn(resp['status'], ('201', '202'))
        self.assertHeaders(resp, 'Container', 'PUT')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        # if the value of metadata is blank, metadata is not registered
        # in the server
        self.assertNotIn('x-container-meta-test-container-meta', resp)

    @test.attr(type='smoke')
    def test_create_container_with_metadata_value(self):
        # create container with metadata value
        container_name = data_utils.rand_name(name='TestContainer')

        metadata = {'test-container-meta': 'Meta1'}
        resp, _ = self.container_client.create_container(
            container_name,
            metadata=metadata)
        self.containers.append(container_name)
        self.assertIn(resp['status'], ('201', '202'))
        self.assertHeaders(resp, 'Container', 'PUT')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertIn('x-container-meta-test-container-meta', resp)
        self.assertEqual(resp['x-container-meta-test-container-meta'],
                         metadata['test-container-meta'])

    @test.attr(type='smoke')
    def test_create_container_with_remove_metadata_key(self):
        # create container with the blank value of remove metadata
        container_name = data_utils.rand_name(name='TestContainer')
        metadata_1 = {'test-container-meta': 'Meta1'}
        self.container_client.create_container(
            container_name,
            metadata=metadata_1)
        self.containers.append(container_name)

        metadata_2 = {'test-container-meta': ''}
        resp, _ = self.container_client.create_container(
            container_name,
            remove_metadata=metadata_2)
        self.assertIn(resp['status'], ('201', '202'))
        self.assertHeaders(resp, 'Container', 'PUT')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta', resp)

    @test.attr(type='smoke')
    def test_create_container_with_remove_metadata_value(self):
        # create container with remove metadata
        container_name = data_utils.rand_name(name='TestContainer')
        metadata = {'test-container-meta': 'Meta1'}
        self.container_client.create_container(container_name,
                                               metadata=metadata)
        self.containers.append(container_name)

        resp, _ = self.container_client.create_container(
            container_name,
            remove_metadata=metadata)
        self.assertIn(resp['status'], ('201', '202'))
        self.assertHeaders(resp, 'Container', 'PUT')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta', resp)

    @test.attr(type='smoke')
    def test_delete_container(self):
        # create a container
        container_name = self._create_container()
        # delete container
        resp, _ = self.container_client.delete_container(container_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'DELETE')

        self.containers.remove(container_name)

    @test.attr(type='smoke')
    def test_list_container_contents(self):
        # get container contents list
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        resp, object_list = self.container_client.list_container_contents(
            container_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    def test_list_container_contents_with_no_object(self):
        # get empty container contents list
        container_name = self._create_container()

        resp, object_list = self.container_client.list_container_contents(
            container_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual('', object_list.strip('\n'))

    @test.attr(type='smoke')
    def test_list_container_contents_with_delimiter(self):
        # get container contents list using delimiter param
        container_name = self._create_container()
        object_name = data_utils.rand_name(name='TestObject/')
        self._create_object(container_name, object_name)

        params = {'delimiter': '/'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name.split('/')[0], object_list.strip('/\n'))

    @test.attr(type='smoke')
    def test_list_container_contents_with_end_marker(self):
        # get container contents list using end_marker param
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        params = {'end_marker': 'ZzzzObject1234567890'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    def test_list_container_contents_with_format_json(self):
        # get container contents list using format_json param
        container_name = self._create_container()
        self._create_object(container_name)

        params = {'format': 'json'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')

        self.assertIsNotNone(object_list)
        self.assertTrue([c['name'] for c in object_list])
        self.assertTrue([c['hash'] for c in object_list])
        self.assertTrue([c['bytes'] for c in object_list])
        self.assertTrue([c['content_type'] for c in object_list])
        self.assertTrue([c['last_modified'] for c in object_list])

    @test.attr(type='smoke')
    def test_list_container_contents_with_format_xml(self):
        # get container contents list using format_xml param
        container_name = self._create_container()
        self._create_object(container_name)

        params = {'format': 'xml'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')

        self.assertIsNotNone(object_list)
        self.assertEqual(object_list.tag, 'container')
        self.assertTrue('name' in object_list.keys())
        self.assertEqual(object_list.find(".//object").tag, 'object')
        self.assertEqual(object_list.find(".//name").tag, 'name')
        self.assertEqual(object_list.find(".//hash").tag, 'hash')
        self.assertEqual(object_list.find(".//bytes").tag, 'bytes')
        self.assertEqual(object_list.find(".//content_type").tag,
                         'content_type')
        self.assertEqual(object_list.find(".//last_modified").tag,
                         'last_modified')

    @test.attr(type='smoke')
    def test_list_container_contents_with_limit(self):
        # get container contents list using limit param
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        params = {'limit': data_utils.rand_int_id(1, 10000)}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    def test_list_container_contents_with_marker(self):
        # get container contents list using marker param
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        params = {'marker': 'AaaaObject1234567890'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    def test_list_container_contents_with_path(self):
        # get container contents list using path param
        container_name = self._create_container()
        object_name = data_utils.rand_name(name='Swift/TestObject')
        self._create_object(container_name, object_name)

        params = {'path': 'Swift'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    def test_list_container_contents_with_prefix(self):
        # get container contents list using prefix param
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        prefix_key = object_name[0:8]
        params = {'prefix': prefix_key}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    def test_list_container_metadata(self):
        # List container metadata
        container_name = self._create_container()

        metadata = {'name': 'Pictures'}
        self.container_client.update_container_metadata(
            container_name,
            metadata=metadata)

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'HEAD')
        self.assertIn('x-container-meta-name', resp)
        self.assertEqual(resp['x-container-meta-name'], metadata['name'])

    @test.attr(type='smoke')
    def test_list_no_container_metadata(self):
        # HEAD container without metadata
        container_name = self._create_container()

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'HEAD')
        self.assertNotIn('x-container-meta-', str(resp))

    @test.attr(type='smoke')
    def test_update_container_metadata_with_create_and_delete_matadata(self):
        # Send one request of adding and deleting metadata
        container_name = data_utils.rand_name(name='TestContainer')
        metadata_1 = {'test-container-meta1': 'Meta1'}
        self.container_client.create_container(container_name,
                                               metadata=metadata_1)
        self.containers.append(container_name)

        metadata_2 = {'test-container-meta2': 'Meta2'}
        resp, _ = self.container_client.update_container_metadata(
            container_name,
            metadata=metadata_2,
            remove_metadata=metadata_1)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta1', resp)
        self.assertIn('x-container-meta-test-container-meta2', resp)
        self.assertEqual(resp['x-container-meta-test-container-meta2'],
                         metadata_2['test-container-meta2'])

    @test.attr(type='smoke')
    def test_update_container_metadata_with_create_metadata(self):
        # update container metadata using add metadata
        container_name = self._create_container()

        metadata = {'test-container-meta1': 'Meta1'}
        resp, _ = self.container_client.update_container_metadata(
            container_name,
            metadata=metadata)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertIn('x-container-meta-test-container-meta1', resp)
        self.assertEqual(resp['x-container-meta-test-container-meta1'],
                         metadata['test-container-meta1'])

    @test.attr(type='smoke')
    def test_update_container_metadata_with_delete_metadata(self):
        # update container metadata using delete metadata
        container_name = data_utils.rand_name(name='TestContainer')
        metadata = {'test-container-meta1': 'Meta1'}
        self.container_client.create_container(container_name,
                                               metadata=metadata)
        self.containers.append(container_name)

        resp, _ = self.container_client.delete_container_metadata(
            container_name,
            metadata=metadata)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta1', resp)

    @test.attr(type='smoke')
    def test_update_container_metadata_with_create_matadata_key(self):
        # update container metadata with a blenk value of metadata
        container_name = self._create_container()

        metadata = {'test-container-meta1': ''}
        resp, _ = self.container_client.update_container_metadata(
            container_name,
            metadata=metadata)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta1', resp)

    @test.attr(type='smoke')
    def test_update_container_metadata_with_delete_metadata_key(self):
        # update container metadata with a blank value of matadata
        container_name = data_utils.rand_name(name='TestContainer')
        metadata = {'test-container-meta1': 'Meta1'}
        self.container_client.create_container(container_name,
                                               metadata=metadata)
        self.containers.append(container_name)

        metadata = {'test-container-meta1': ''}
        resp, _ = self.container_client.delete_container_metadata(
            container_name,
            metadata=metadata)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(container_name)
        self.assertNotIn('x-container-meta-test-container-meta1', resp)
