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

from tempest_lib.common.utils import data_utils

from tempest.api.object_storage import base
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
    @test.idempotent_id('92139d73-7819-4db1-85f8-3f2f22a8d91f')
    def test_create_container(self):
        container_name = data_utils.rand_name(name='TestContainer')
        resp, body = self.container_client.create_container(container_name)
        self.containers.append(container_name)
        self.assertHeaders(resp, 'Container', 'PUT')

    @test.attr(type='smoke')
    @test.idempotent_id('49f866ed-d6af-4395-93e7-4187eb56d322')
    def test_create_container_overwrite(self):
        # overwrite container with the same name
        container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.create_container(container_name)
        self.containers.append(container_name)

        resp, _ = self.container_client.create_container(container_name)
        self.assertHeaders(resp, 'Container', 'PUT')

    @test.attr(type='smoke')
    @test.idempotent_id('c2ac4d59-d0f5-40d5-ba19-0635056d48cd')
    def test_create_container_with_metadata_key(self):
        # create container with the blank value of metadata
        container_name = data_utils.rand_name(name='TestContainer')
        metadata = {'test-container-meta': ''}
        resp, _ = self.container_client.create_container(
            container_name,
            metadata=metadata)
        self.containers.append(container_name)
        self.assertHeaders(resp, 'Container', 'PUT')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        # if the value of metadata is blank, metadata is not registered
        # in the server
        self.assertNotIn('x-container-meta-test-container-meta', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('e1e8df32-7b22-44e1-aa08-ccfd8d446b58')
    def test_create_container_with_metadata_value(self):
        # create container with metadata value
        container_name = data_utils.rand_name(name='TestContainer')

        metadata = {'test-container-meta': 'Meta1'}
        resp, _ = self.container_client.create_container(
            container_name,
            metadata=metadata)
        self.containers.append(container_name)
        self.assertHeaders(resp, 'Container', 'PUT')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertIn('x-container-meta-test-container-meta', resp)
        self.assertEqual(resp['x-container-meta-test-container-meta'],
                         metadata['test-container-meta'])

    @test.attr(type='smoke')
    @test.idempotent_id('24d16451-1c0c-4e4f-b59c-9840a3aba40e')
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
        self.assertHeaders(resp, 'Container', 'PUT')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('8a21ebad-a5c7-4e29-b428-384edc8cd156')
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
        self.assertHeaders(resp, 'Container', 'PUT')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('95d3a249-b702-4082-a2c4-14bb860cf06a')
    def test_delete_container(self):
        # create a container
        container_name = self._create_container()
        # delete container, success asserted within
        resp, _ = self.container_client.delete_container(container_name)
        self.assertHeaders(resp, 'Container', 'DELETE')
        self.containers.remove(container_name)

    @test.attr(type='smoke')
    @test.idempotent_id('312ff6bd-5290-497f-bda1-7c5fec6697ab')
    def test_list_container_contents(self):
        # get container contents list
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        resp, object_list = self.container_client.list_container_contents(
            container_name)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    @test.idempotent_id('4646ac2d-9bfb-4c7d-a3c5-0f527402b3df')
    def test_list_container_contents_with_no_object(self):
        # get empty container contents list
        container_name = self._create_container()

        resp, object_list = self.container_client.list_container_contents(
            container_name)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual('', object_list.strip('\n'))

    @test.attr(type='smoke')
    @test.idempotent_id('fe323a32-57b9-4704-a996-2e68f83b09bc')
    def test_list_container_contents_with_delimiter(self):
        # get container contents list using delimiter param
        container_name = self._create_container()
        object_name = data_utils.rand_name(name='TestObject/')
        self._create_object(container_name, object_name)

        params = {'delimiter': '/'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name.split('/')[0], object_list.strip('/\n'))

    @test.attr(type='smoke')
    @test.idempotent_id('55b4fa5c-e12e-4ca9-8fcf-a79afe118522')
    def test_list_container_contents_with_end_marker(self):
        # get container contents list using end_marker param
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        params = {'end_marker': 'ZzzzObject1234567890'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    @test.idempotent_id('196f5034-6ab0-4032-9da9-a937bbb9fba9')
    def test_list_container_contents_with_format_json(self):
        # get container contents list using format_json param
        container_name = self._create_container()
        self._create_object(container_name)

        params = {'format': 'json'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertHeaders(resp, 'Container', 'GET')

        self.assertIsNotNone(object_list)
        self.assertTrue([c['name'] for c in object_list])
        self.assertTrue([c['hash'] for c in object_list])
        self.assertTrue([c['bytes'] for c in object_list])
        self.assertTrue([c['content_type'] for c in object_list])
        self.assertTrue([c['last_modified'] for c in object_list])

    @test.attr(type='smoke')
    @test.idempotent_id('655a53ca-4d15-408c-a377-f4c6dbd0a1fa')
    def test_list_container_contents_with_format_xml(self):
        # get container contents list using format_xml param
        container_name = self._create_container()
        self._create_object(container_name)

        params = {'format': 'xml'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
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
    @test.idempotent_id('297ec38b-2b61-4ff4-bcd1-7fa055e97b61')
    def test_list_container_contents_with_limit(self):
        # get container contents list using limit param
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        params = {'limit': data_utils.rand_int_id(1, 10000)}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    @test.idempotent_id('c31ddc63-2a58-4f6b-b25c-94d2937e6867')
    def test_list_container_contents_with_marker(self):
        # get container contents list using marker param
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        params = {'marker': 'AaaaObject1234567890'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    @test.idempotent_id('58ca6cc9-6af0-408d-aaec-2a6a7b2f0df9')
    def test_list_container_contents_with_path(self):
        # get container contents list using path param
        container_name = self._create_container()
        object_name = data_utils.rand_name(name='Swift/TestObject')
        self._create_object(container_name, object_name)

        params = {'path': 'Swift'}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    @test.idempotent_id('77e742c7-caf2-4ec9-8aa4-f7d509a3344c')
    def test_list_container_contents_with_prefix(self):
        # get container contents list using prefix param
        container_name = self._create_container()
        object_name = self._create_object(container_name)

        prefix_key = object_name[0:8]
        params = {'prefix': prefix_key}
        resp, object_list = self.container_client.list_container_contents(
            container_name,
            params=params)
        self.assertHeaders(resp, 'Container', 'GET')
        self.assertEqual(object_name, object_list.strip('\n'))

    @test.attr(type='smoke')
    @test.idempotent_id('96e68f0e-19ec-4aa2-86f3-adc6a45e14dd')
    def test_list_container_metadata(self):
        # List container metadata
        container_name = self._create_container()

        metadata = {'name': 'Pictures'}
        self.container_client.update_container_metadata(
            container_name,
            metadata=metadata)

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertHeaders(resp, 'Container', 'HEAD')
        self.assertIn('x-container-meta-name', resp)
        self.assertEqual(resp['x-container-meta-name'], metadata['name'])

    @test.attr(type='smoke')
    @test.idempotent_id('a2faf936-6b13-4f8d-92a2-c2278355821e')
    def test_list_no_container_metadata(self):
        # HEAD container without metadata
        container_name = self._create_container()

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertHeaders(resp, 'Container', 'HEAD')
        self.assertNotIn('x-container-meta-', str(resp))

    @test.attr(type='smoke')
    @test.idempotent_id('cf19bc0b-7e16-4a5a-aaed-cb0c2fe8deef')
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
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta1', resp)
        self.assertIn('x-container-meta-test-container-meta2', resp)
        self.assertEqual(resp['x-container-meta-test-container-meta2'],
                         metadata_2['test-container-meta2'])

    @test.attr(type='smoke')
    @test.idempotent_id('2ae5f295-4bf1-4e04-bfad-21e54b62cec5')
    def test_update_container_metadata_with_create_metadata(self):
        # update container metadata using add metadata
        container_name = self._create_container()

        metadata = {'test-container-meta1': 'Meta1'}
        resp, _ = self.container_client.update_container_metadata(
            container_name,
            metadata=metadata)
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertIn('x-container-meta-test-container-meta1', resp)
        self.assertEqual(resp['x-container-meta-test-container-meta1'],
                         metadata['test-container-meta1'])

    @test.attr(type='smoke')
    @test.idempotent_id('3a5ce7d4-6e4b-47d0-9d87-7cd42c325094')
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
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta1', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('31f40a5f-6a52-4314-8794-cd89baed3040')
    def test_update_container_metadata_with_create_matadata_key(self):
        # update container metadata with a blenk value of metadata
        container_name = self._create_container()

        metadata = {'test-container-meta1': ''}
        resp, _ = self.container_client.update_container_metadata(
            container_name,
            metadata=metadata)
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(
            container_name)
        self.assertNotIn('x-container-meta-test-container-meta1', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('a2e36378-6f1f-43f4-840a-ffd9cfd61914')
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
        self.assertHeaders(resp, 'Container', 'POST')

        resp, _ = self.container_client.list_container_metadata(container_name)
        self.assertNotIn('x-container-meta-test-container-meta1', resp)
