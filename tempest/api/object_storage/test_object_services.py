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

import random
import re
import time
import zlib

from oslo_utils.secretutils import md5
from tempest.api.object_storage import base
from tempest.common import custom_matchers
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ObjectTest(base.BaseObjectTest):
    """Test storage object"""

    @classmethod
    def resource_setup(cls):
        super(ObjectTest, cls).resource_setup()
        cls.container_name = cls.create_container()

    @classmethod
    def resource_cleanup(cls):
        cls.delete_containers()
        super(ObjectTest, cls).resource_cleanup()

    def _upload_segments(self):
        # create object
        object_name = data_utils.rand_name(name='LObject')
        data = data_utils.arbitrary_string()
        segments = 10
        data_segments = [data + str(i) for i in range(segments)]
        # uploading segments
        for i in range(segments):
            obj_name = "%s/%s" % (object_name, i)
            self.object_client.create_object(
                self.container_name, obj_name, data_segments[i])

        return object_name, data_segments

    def _copy_object_2d(self, src_object_name, metadata=None):
        dst_object_name = data_utils.rand_name(name='TestObject')
        resp, _ = self.object_client.copy_object_2d_way(self.container_name,
                                                        src_object_name,
                                                        dst_object_name,
                                                        metadata=metadata)
        return dst_object_name, resp

    def _check_copied_obj(self, dst_object_name, src_body,
                          in_meta=None, not_in_meta=None):
        resp, dest_body = self.object_client.get_object(self.container_name,
                                                        dst_object_name)

        self.assertEqual(src_body, dest_body)
        if in_meta:
            for meta_key in in_meta:
                self.assertIn('x-object-meta-' + meta_key, resp)
        if not_in_meta:
            for meta_key in not_in_meta:
                self.assertNotIn('x-object-meta-' + meta_key, resp)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('5b4ce26f-3545-46c9-a2ba-5754358a4c62')
    def test_create_object(self):
        """Test creating object and checking the object's uploaded content"""
        # create object
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # create another object
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @decorators.idempotent_id('5daebb1d-f0d5-4dc9-b541-69672eff00b0')
    def test_create_object_with_content_disposition(self):
        """Test creating object with content-disposition"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        metadata = {}
        metadata['content-disposition'] = 'inline'
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data,
            metadata=metadata)
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=None)
        self.assertIn('content-disposition', resp)
        self.assertEqual(resp['content-disposition'], 'inline')
        self.assertEqual(body, data)

    @decorators.idempotent_id('605f8317-f945-4bee-ae91-013f1da8f0a0')
    def test_create_object_with_content_encoding(self):
        """Test creating object with content-encoding"""
        object_name = data_utils.rand_name(name='TestObject')

        # put compressed string
        data_before = b'x' * 2000
        data = zlib.compress(data_before)
        metadata = {}
        metadata['content-encoding'] = 'deflate'

        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data,
            metadata=metadata)
        self.assertHeaders(resp, 'Object', 'PUT')

        # download compressed object
        metadata = {}
        metadata['accept-encoding'] = 'deflate'
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=metadata)
        self.assertEqual(body, data_before)

    @decorators.idempotent_id('73820093-0503-40b1-a478-edf0e69c7d1f')
    def test_create_object_with_etag(self):
        """Test creating object with Etag"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        create_md5 = md5(data, usedforsecurity=False).hexdigest()
        metadata = {'Etag': create_md5}
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data,
            metadata=metadata)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @decorators.idempotent_id('84dafe57-9666-4f6d-84c8-0814d37923b8')
    def test_create_object_with_expect_continue(self):
        """Test creating object with expect_continue"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()

        status, _ = self.object_client.create_object_continue(
            self.container_name, object_name, data)

        self.assertEqual(status, 201)

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @decorators.idempotent_id('4f84422a-e2f2-4403-b601-726a4220b54e')
    @decorators.skip_because(bug='1905432')
    def test_create_object_with_transfer_encoding(self):
        """Test creating object with transfer_encoding"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes(1024)
        headers = {'Transfer-Encoding': 'chunked'}
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data=data_utils.chunkify(data, 512),
            headers=headers,
            chunked=True)

        self.assertHeaders(resp, 'Object', 'PUT')

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @decorators.idempotent_id('0f3d62a6-47e3-4554-b0e5-1a5dc372d501')
    def test_create_object_with_x_fresh_metadata(self):
        """Test creating object with x-fresh-metadata

        The previous added metadata will be cleared.
        """
        object_name_base = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        metadata_1 = {'X-Object-Meta-test-meta': 'Meta'}
        self.object_client.create_object(self.container_name,
                                         object_name_base,
                                         data,
                                         metadata=metadata_1)
        object_name = data_utils.rand_name(name='TestObject')
        metadata_2 = {'X-Copy-From': '%s/%s' % (self.container_name,
                                                object_name_base),
                      'X-Fresh-Metadata': 'true'}
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            '',
            metadata=metadata_2)
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)
        self.assertEqual(data, body)

    @decorators.idempotent_id('1c7ed3e4-2099-406b-b843-5301d4811baf')
    def test_create_object_with_x_object_meta(self):
        """Test creating object with x-object-meta"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        metadata = {'X-Object-Meta-test-meta': 'Meta'}
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data,
            metadata=metadata)
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')
        self.assertEqual(data, body)

    @decorators.idempotent_id('e4183917-33db-4153-85cc-4dacbb938865')
    def test_create_object_with_x_object_metakey(self):
        """Test creating object with the blank value of metadata"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        metadata = {'X-Object-Meta-test-meta': ''}
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data,
            metadata=metadata)
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], '')
        self.assertEqual(data, body)

    @decorators.idempotent_id('ce798afc-b278-45de-a5ce-2ea124b98b99')
    def test_create_object_with_x_remove_object_meta(self):
        """Test creating object with x-remove-object-meta

        The metadata will be removed from the object.
        """
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        metadata_add = {'X-Object-Meta-test-meta': 'Meta'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=metadata_add)
        metadata_remove = {'X-Remove-Object-Meta-test-meta': 'Meta'}
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data,
            metadata=metadata_remove)
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)
        self.assertEqual(data, body)

    @decorators.idempotent_id('ad21e342-7916-4f9e-ab62-a1f885f2aaf9')
    def test_create_object_with_x_remove_object_metakey(self):
        """Test creating object with the blank value of remove metadata

        Creating object with blank metadata 'X-Remove-Object-Meta-test-meta',
        metadata 'x-object-meta-test-meta' will be removed from the object.
        """
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        metadata_add = {'X-Object-Meta-test-meta': 'Meta'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=metadata_add)
        metadata_remove = {'X-Remove-Object-Meta-test-meta': ''}
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data,
            metadata=metadata_remove)
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)
        self.assertEqual(data, body)

    @decorators.idempotent_id('17738d45-03bd-4d45-9e0b-7b2f58f98687')
    def test_delete_object(self):
        """Test deleting object"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # delete object
        resp, _ = self.object_client.delete_object(self.container_name,
                                                   object_name)
        self.assertHeaders(resp, 'Object', 'DELETE')

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('7a94c25d-66e6-434c-9c38-97d4e2c29945')
    def test_update_object_metadata(self):
        """Test updating object metadata"""
        object_name, _ = self.create_object(self.container_name)

        metadata = {'X-Object-Meta-test-meta': 'Meta'}
        resp, _ = self.object_client.create_or_update_object_metadata(
            self.container_name,
            object_name,
            headers=metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')

    @decorators.idempotent_id('48650ed0-c189-4e1e-ad6b-1d4770c6e134')
    def test_update_object_metadata_with_remove_metadata(self):
        """Test updating object metadata with remove metadata"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        create_metadata = {'X-Object-Meta-test-meta1': 'Meta1'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        update_metadata = {'X-Remove-Object-Meta-test-meta1': 'Meta1'}
        resp, _ = self.object_client.create_or_update_object_metadata(
            self.container_name,
            object_name,
            headers=update_metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta1', resp)

    @decorators.idempotent_id('f726174b-2ded-4708-bff7-729d12ce1f84')
    def test_update_object_metadata_with_create_and_remove_metadata(self):
        """Test updating object with creation and deletion of metadata

        Update object with creation and deletion of metadata with one
        request, both operations will succeed.
        """
        # creation and deletion of metadata with one request
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        create_metadata = {'X-Object-Meta-test-meta1': 'Meta1'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        update_metadata = {'X-Object-Meta-test-meta2': 'Meta2',
                           'X-Remove-Object-Meta-test-meta1': 'Meta1'}
        resp, _ = self.object_client.create_or_update_object_metadata(
            self.container_name,
            object_name,
            headers=update_metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta1', resp)
        self.assertIn('x-object-meta-test-meta2', resp)
        self.assertEqual(resp['x-object-meta-test-meta2'], 'Meta2')

    @decorators.idempotent_id('08854588-6449-4bb7-8cca-f2e1040f5e6f')
    def test_update_object_metadata_with_x_object_manifest(self):
        """Test updating object metadata with x_object_manifest"""
        # uploading segments
        object_name, _ = self._upload_segments()
        # creating a manifest file
        data_empty = ''
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data_empty,
                                         metadata=None)
        object_prefix = '%s/%s' % (self.container_name, object_name)
        update_metadata = {'X-Object-Manifest': object_prefix}
        resp, _ = self.object_client.create_or_update_object_metadata(
            self.container_name,
            object_name,
            headers=update_metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-manifest', resp)
        self.assertNotEmpty(resp['x-object-manifest'])

    @decorators.idempotent_id('0dbbe89c-6811-4d84-a2df-eca2bdd40c0e')
    def test_update_object_metadata_with_x_object_metakey(self):
        """Test updating object metadata with a blank value of metadata"""
        object_name, _ = self.create_object(self.container_name)

        update_metadata = {'X-Object-Meta-test-meta': ''}
        resp, _ = self.object_client.create_or_update_object_metadata(
            self.container_name,
            object_name,
            headers=update_metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], '')

    @decorators.idempotent_id('9a88dca4-b684-425b-806f-306cd0e57e42')
    def test_update_object_metadata_with_x_remove_object_metakey(self):
        """Test updating object metadata with blank remove metadata value"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        create_metadata = {'X-Object-Meta-test-meta': 'Meta'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        update_metadata = {'X-Remove-Object-Meta-test-meta': ''}
        resp, _ = self.object_client.create_or_update_object_metadata(
            self.container_name,
            object_name,
            headers=update_metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('9a447cf6-de06-48de-8226-a8c6ed31caf2')
    def test_list_object_metadata(self):
        """Test listing object metadata"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        metadata = {'X-Object-Meta-test-meta': 'Meta'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=metadata)

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertHeaders(resp, 'Object', 'HEAD')
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')

    @decorators.idempotent_id('170fb90e-f5c3-4b1f-ae1b-a18810821172')
    def test_list_no_object_metadata(self):
        """Test listing object metadata for object without metadata"""
        object_name, _ = self.create_object(self.container_name)

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertHeaders(resp, 'Object', 'HEAD')
        self.assertNotIn('x-object-meta-', str(resp))

    @decorators.idempotent_id('23a3674c-d6de-46c3-86af-ff92bfc8a3da')
    def test_list_object_metadata_with_x_object_manifest(self):
        """Test getting object metadata with x_object_manifest"""
        # uploading segments
        object_name, _ = self._upload_segments()
        # creating a manifest file
        object_prefix = '%s/%s' % (self.container_name, object_name)
        metadata = {'X-Object-Manifest': object_prefix}
        data_empty = ''
        resp, _ = self.object_client.create_object(
            self.container_name,
            object_name,
            data_empty,
            metadata=metadata)

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)

        # Check only the existence of common headers with custom matcher
        self.assertThat(resp, custom_matchers.ExistsAllResponseHeaders(
                        'Object', 'HEAD'))
        self.assertIn('x-object-manifest', resp)

        # Etag value of a large object is enclosed in double-quotations.
        # This is a special case, therefore the formats of response headers
        # are checked without a custom matcher.
        self.assertTrue(resp['etag'].startswith('\"'))
        self.assertTrue(resp['etag'].endswith('\"'))
        self.assertTrue(resp['etag'].strip('\"').isalnum())
        self.assertTrue(re.match(r"^\d+\.?\d*\Z", resp['x-timestamp']))
        self.assertNotEmpty(resp['content-type'])
        self.assertTrue(re.match("^tx[0-9a-f]{21}-[0-9a-f]{10}.*",
                                 resp['x-trans-id']))
        self.assertNotEmpty(resp['date'])
        self.assertEqual(resp['accept-ranges'], 'bytes')
        self.assertEqual(resp['x-object-manifest'],
                         '%s/%s' % (self.container_name, object_name))

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('02610ba7-86b7-4272-9ed8-aa8d417cb3cd')
    def test_get_object(self):
        """Test retrieving object's data (in response body)"""

        # create object
        object_name, data = self.create_object(self.container_name)
        # get object
        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertHeaders(resp, 'Object', 'GET')

        self.assertEqual(body, data)

    @decorators.idempotent_id('005f9bf6-e06d-41ec-968e-96c78e0b1d82')
    def test_get_object_with_metadata(self):
        """Test getting object with metadata"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        metadata = {'X-Object-Meta-test-meta': 'Meta'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=metadata)
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=None)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')
        self.assertEqual(body, data)

    @decorators.idempotent_id('05a1890e-7db9-4a6c-90a8-ce998a2bddfa')
    def test_get_object_with_range(self):
        """Test getting object with range"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes(100)
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=None)
        rand_num = random.randint(3, len(data) - 1)
        metadata = {'Range': 'bytes=%s-%s' % (rand_num - 3, rand_num - 1)}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data[rand_num - 3: rand_num])

    @decorators.idempotent_id('11b4515b-7ba7-4ca8-8838-357ded86fc10')
    def test_get_object_with_x_object_manifest(self):
        """Test getting object with x_object_manifest"""

        # uploading segments
        object_name, data_segments = self._upload_segments()
        # creating a manifest file
        object_prefix = '%s/%s' % (self.container_name, object_name)
        metadata = {'X-Object-Manifest': object_prefix}
        data_empty = ''
        resp, body = self.object_client.create_object(
            self.container_name,
            object_name,
            data_empty,
            metadata=metadata)

        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=None)

        # Check only the existence of common headers with custom matcher
        self.assertThat(resp, custom_matchers.ExistsAllResponseHeaders(
                        'Object', 'GET'))
        self.assertIn('x-object-manifest', resp)

        # Etag value of a large object is enclosed in double-quotations.
        # This is a special case, therefore the formats of response headers
        # are checked without a custom matcher.
        self.assertTrue(resp['etag'].startswith('\"'))
        self.assertTrue(resp['etag'].endswith('\"'))
        self.assertTrue(resp['etag'].strip('\"').isalnum())
        self.assertTrue(re.match(r"^\d+\.?\d*\Z", resp['x-timestamp']))
        self.assertNotEmpty(resp['content-type'])
        self.assertTrue(re.match("^tx[0-9a-f]{21}-[0-9a-f]{10}.*",
                                 resp['x-trans-id']))
        self.assertNotEmpty(resp['date'])
        self.assertEqual(resp['accept-ranges'], 'bytes')
        self.assertEqual(resp['x-object-manifest'],
                         '%s/%s' % (self.container_name, object_name))

        self.assertEqual(''.join(data_segments), body.decode())

    @decorators.idempotent_id('c05b4013-e4de-47af-be84-e598062b16fc')
    def test_get_object_with_if_match(self):
        """Test getting object with if_match"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes(10)
        create_md5 = md5(data, usedforsecurity=False).hexdigest()
        create_metadata = {'Etag': create_md5}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        list_metadata = {'If-Match': create_md5}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @decorators.idempotent_id('be133639-e5d2-4313-9b1f-2d59fc054a16')
    def test_get_object_with_if_modified_since(self):
        """Test getting object with if_modified_since"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        time_now = time.time()
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=None)

        http_date = time.ctime(time_now - 86400)
        list_metadata = {'If-Modified-Since': http_date}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @decorators.idempotent_id('641500d5-1612-4042-a04d-01fc4528bc30')
    def test_get_object_with_if_none_match(self):
        """Test getting object with if_none_match"""
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.random_bytes()
        create_md5 = md5(data, usedforsecurity=False).hexdigest()
        create_metadata = {'Etag': create_md5}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        list_data = data_utils.random_bytes()
        list_md5 = md5(list_data, usedforsecurity=False).hexdigest()
        list_metadata = {'If-None-Match': list_md5}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @decorators.idempotent_id('0aa1201c-10aa-467a-bee7-63cbdd463152')
    def test_get_object_with_if_unmodified_since(self):
        """Test getting object with if_unmodified_since"""
        object_name, data = self.create_object(self.container_name)

        time_now = time.time()
        http_date = time.ctime(time_now + 86400)
        list_metadata = {'If-Unmodified-Since': http_date}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @decorators.idempotent_id('94587078-475f-48f9-a40f-389c246e31cd')
    def test_get_object_with_x_newest(self):
        """Test getting object with x_newest"""
        object_name, data = self.create_object(self.container_name)

        list_metadata = {'X-Newest': 'true'}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @decorators.idempotent_id('1a9ab572-1b66-4981-8c21-416e2a5e6011')
    def test_copy_object_in_same_container(self):
        """Test copying object to another object in same container"""
        # create source object
        src_object_name = data_utils.rand_name(name='SrcObject')
        src_data = data_utils.random_bytes(size=len(src_object_name) * 2)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   src_object_name,
                                                   src_data)
        # create destination object
        dst_object_name = data_utils.rand_name(name='DstObject')
        dst_data = data_utils.random_bytes(size=len(dst_object_name) * 3)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   dst_object_name,
                                                   dst_data)
        # copy source object to destination
        headers = {}
        headers['X-Copy-From'] = "%s/%s" % (str(self.container_name),
                                            str(src_object_name))
        resp, body = self.object_client.create_object(self.container_name,
                                                      dst_object_name,
                                                      data=None,
                                                      headers=headers)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check data
        resp, body = self.object_client.get_object(self.container_name,
                                                   dst_object_name)
        self.assertEqual(body, src_data)

    @decorators.idempotent_id('2248abba-415d-410b-9c30-22dff9cd6e67')
    def test_copy_object_to_itself(self):
        """Test changing the content type of an existing object"""

        # create object
        object_name, _ = self.create_object(self.container_name)
        # get the old content type
        resp_tmp, _ = self.object_client.list_object_metadata(
            self.container_name, object_name)
        # change the content type of the object
        metadata = {'content-type': 'text/plain; charset=UTF-8'}
        self.assertNotEqual(resp_tmp['content-type'], metadata['content-type'])
        headers = {}
        headers['X-Copy-From'] = "%s/%s" % (str(self.container_name),
                                            str(object_name))
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name,
                                                   data=None,
                                                   metadata=metadata,
                                                   headers=headers)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check the content type
        resp, _ = self.object_client.list_object_metadata(self.container_name,
                                                          object_name)
        self.assertEqual(resp['content-type'], metadata['content-type'])

    @decorators.idempotent_id('06f90388-2d0e-40aa-934c-e9a8833e958a')
    def test_copy_object_2d_way(self):
        """Test copying object's data to the new object using COPY"""
        # create source object
        src_object_name = data_utils.rand_name(name='SrcObject')
        src_data = data_utils.random_bytes(size=len(src_object_name) * 2)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   src_object_name, src_data)
        # create destination object
        dst_object_name = data_utils.rand_name(name='DstObject')
        dst_data = data_utils.random_bytes(size=len(dst_object_name) * 3)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   dst_object_name, dst_data)
        # copy source object to destination
        resp, _ = self.object_client.copy_object_2d_way(self.container_name,
                                                        src_object_name,
                                                        dst_object_name)
        self.assertHeaders(resp, 'Object', 'COPY')
        self.assertEqual(
            resp['x-copied-from'],
            self.container_name + "/" + src_object_name)

        # check data
        self._check_copied_obj(dst_object_name, src_data)

    @decorators.idempotent_id('aa467252-44f3-472a-b5ae-5b57c3c9c147')
    def test_copy_object_across_containers(self):
        """Test copying object to another container"""
        # create a container to use as a source container
        src_container_name = data_utils.rand_name(name='TestSourceContainer')
        self.container_client.update_container(src_container_name)
        self.containers.append(src_container_name)
        # create a container to use as a destination container
        dst_container_name = data_utils.rand_name(
            name='TestDestinationContainer')
        self.container_client.update_container(dst_container_name)
        self.containers.append(dst_container_name)
        # create object in source container
        object_name = data_utils.rand_name(name='Object')
        data = data_utils.random_bytes(size=len(object_name) * 2)
        resp, _ = self.object_client.create_object(src_container_name,
                                                   object_name, data)
        # set object metadata
        meta_key = data_utils.rand_name(name='test')
        meta_value = data_utils.rand_name(name='MetaValue')
        orig_metadata = {'X-Object-Meta-' + meta_key: meta_value}
        resp, _ = self.object_client.create_or_update_object_metadata(
            src_container_name,
            object_name,
            headers=orig_metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        # copy object from source container to destination container
        headers = {}
        headers['X-Copy-From'] = "%s/%s" % (str(src_container_name),
                                            str(object_name))
        resp, body = self.object_client.create_object(dst_container_name,
                                                      object_name,
                                                      data=None,
                                                      headers=headers)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check if object is present in destination container
        resp, body = self.object_client.get_object(dst_container_name,
                                                   object_name)
        self.assertEqual(body, data)
        actual_meta_key = 'x-object-meta-' + meta_key
        self.assertIn(actual_meta_key, resp)
        self.assertEqual(resp[actual_meta_key], meta_value)

    @decorators.idempotent_id('5a9e2cc6-85b6-46fc-916d-0cbb7a88e5fd')
    def test_copy_object_with_x_fresh_metadata(self):
        """Test copying objectwith x_fresh_metadata"""
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_object_name, data = self.create_object(self.container_name,
                                                   metadata=metadata)

        # copy source object with x_fresh_metadata header
        metadata = {'X-Fresh-Metadata': 'true'}
        dst_object_name, resp = self._copy_object_2d(src_object_name,
                                                     metadata)

        self.assertHeaders(resp, 'Object', 'COPY')

        self.assertNotIn('x-object-meta-src', resp)
        self.assertEqual(resp['x-copied-from'],
                         self.container_name + "/" + src_object_name)

        # check that destination object does NOT have any object-meta
        self._check_copied_obj(dst_object_name, data, not_in_meta=["src"])

    @decorators.idempotent_id('a28a8b99-e701-4d7e-9d84-3b66f121460b')
    def test_copy_object_with_x_object_metakey(self):
        """Test copying object with x_object_metakey"""
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_obj_name, data = self.create_object(self.container_name,
                                                metadata=metadata)

        # copy source object to destination with x-object-meta-key
        metadata = {'x-object-meta-test': ''}
        dst_obj_name, resp = self._copy_object_2d(src_obj_name, metadata)

        self.assertHeaders(resp, 'Object', 'COPY')

        expected = {'x-object-meta-test': '',
                    'x-object-meta-src': 'src_value',
                    'x-copied-from': self.container_name + "/" + src_obj_name}
        for key, value in expected.items():
            self.assertIn(key, resp)
            self.assertEqual(value, resp[key])

        # check destination object
        self._check_copied_obj(dst_obj_name, data, in_meta=["test", "src"])

    @decorators.idempotent_id('edabedca-24c3-4322-9b70-d6d9f942a074')
    def test_copy_object_with_x_object_meta(self):
        """Test copying object with x_object_meta"""
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_obj_name, data = self.create_object(self.container_name,
                                                metadata=metadata)

        # copy source object to destination with object metadata
        metadata = {'x-object-meta-test': 'value'}
        dst_obj_name, resp = self._copy_object_2d(src_obj_name, metadata)

        self.assertHeaders(resp, 'Object', 'COPY')

        expected = {'x-object-meta-test': 'value',
                    'x-object-meta-src': 'src_value',
                    'x-copied-from': self.container_name + "/" + src_obj_name}
        for key, value in expected.items():
            self.assertIn(key, resp)
            self.assertEqual(value, resp[key])

        # check destination object
        self._check_copied_obj(dst_obj_name, data, in_meta=["test", "src"])

    @decorators.idempotent_id('e3e6a64a-9f50-4955-b987-6ce6767c97fb')
    def test_object_upload_in_segments(self):
        """Test uploading object in segments"""
        # create object
        object_name = data_utils.rand_name(name='LObject')
        data = data_utils.arbitrary_string()
        segments = 10
        data_segments = [data + str(i) for i in range(segments)]
        # uploading segments
        for i in range(segments):
            obj_name = "%s/%s" % (object_name, i)
            resp, _ = self.object_client.create_object(
                self.container_name, obj_name, data_segments[i])
        # creating a manifest file
        metadata = {'X-Object-Manifest': '%s/%s/'
                    % (self.container_name, object_name)}
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data='')
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, _ = self.object_client.create_or_update_object_metadata(
            self.container_name, object_name, headers=metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name, object_name)

        # Etag value of a large object is enclosed in double-quotations.
        # After etag quotes are checked they are removed and the response is
        # checked if all common headers are present and well formatted
        self.assertTrue(resp['etag'].startswith('\"'))
        self.assertTrue(resp['etag'].endswith('\"'))
        resp['etag'] = resp['etag'].strip('"')
        self.assertHeaders(resp, 'Object', 'HEAD')

        self.assertIn('x-object-manifest', resp)
        self.assertEqual(resp['x-object-manifest'],
                         '%s/%s/' % (self.container_name, object_name))

        # downloading the object
        resp, body = self.object_client.get_object(
            self.container_name, object_name)
        self.assertEqual(''.join(data_segments), body.decode())

    @decorators.idempotent_id('50d01f12-526f-4360-9ac2-75dd508d7b68')
    def test_get_object_if_different(self):
        """Test getting object content only when the local file is different

        http://en.wikipedia.org/wiki/HTTP_ETag
        Make a conditional request for an object using the If-None-Match
        header, it should get downloaded only if the local file is different,
        otherwise the response code should be 304 Not Modified
        """
        object_name, data = self.create_object(self.container_name)
        # local copy is identical, no download
        object_md5 = md5(data, usedforsecurity=False).hexdigest()
        headers = {'If-None-Match': object_md5}
        url = "%s/%s" % (self.container_name, object_name)
        resp, _ = self.object_client.get(url, headers=headers)
        self.assertEqual(resp['status'], '304')

        # When the file is not downloaded from Swift server, response does
        # not contain 'X-Timestamp' header. This is the special case, therefore
        # the existence of response headers is checked without custom matcher.
        self.assertIn('date', resp)
        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

        # local copy is different, download
        local_data = "something different"
        other_md5 = md5(local_data.encode(), usedforsecurity=False).hexdigest()
        headers = {'If-None-Match': other_md5}
        resp, _ = self.object_client.get(url, headers=headers)
        self.assertHeaders(resp, 'Object', 'GET')


class PublicObjectTest(base.BaseObjectTest):
    """Test public storage object"""

    credentials = [['operator', CONF.object_storage.operator_role],
                   ['operator_alt', CONF.object_storage.operator_role]]

    @classmethod
    def setup_credentials(cls):
        super(PublicObjectTest, cls).setup_credentials()
        cls.os_alt = cls.os_roles_operator_alt

    @classmethod
    def setup_clients(cls):
        super(PublicObjectTest, cls).setup_clients()
        cls.object_client_alt = cls.os_alt.object_client

    def setUp(self):
        super(PublicObjectTest, self).setUp()
        self.container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.update_container(self.container_name)

    def tearDown(self):
        self.delete_containers([self.container_name])
        super(PublicObjectTest, self).tearDown()

    @decorators.idempotent_id('07c9cf95-c0d4-4b49-b9c8-0ef2c9b27193')
    def test_access_public_container_object_without_using_creds(self):
        """Test accessing public container object without using credentials

        Make container public-readable and access an object in it object
        anonymously, without using credentials.
        """
        # update container metadata to make it publicly readable
        cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
        resp_meta, body = (
            self.container_client.create_update_or_delete_container_metadata(
                self.container_name,
                create_update_metadata=cont_headers,
                create_update_metadata_prefix=''))
        self.assertHeaders(resp_meta, 'Container', 'POST')

        # create object
        object_name = data_utils.rand_name(name='Object')
        data = data_utils.random_bytes(size=len(object_name))
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertHeaders(resp, 'Object', 'PUT')

        # list container metadata
        resp_meta, _ = self.container_client.list_container_metadata(
            self.container_name)
        self.assertHeaders(resp_meta, 'Container', 'HEAD')

        self.assertIn('x-container-read', resp_meta)
        self.assertEqual(resp_meta['x-container-read'], '.r:*,.rlistings')

        # trying to get object with empty headers as it is public readable
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )
        resp, body = self.object_client.get_object(
            self.container_name, object_name)
        self.assertHeaders(resp, 'Object', 'GET')

        self.assertEqual(body, data)

    @decorators.idempotent_id('54e2a2fe-42dc-491b-8270-8e4217dd4cdc')
    def test_access_public_object_with_another_user_creds(self):
        """Test accessing public object with another user's credentials

        Make container public-readable and access an object in it using
        another user's credentials.
        """
        cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
        resp_meta, body = (
            self.container_client.create_update_or_delete_container_metadata(
                self.container_name, create_update_metadata=cont_headers,
                create_update_metadata_prefix=''))
        self.assertHeaders(resp_meta, 'Container', 'POST')

        # create object
        object_name = data_utils.rand_name(name='Object')
        data = data_utils.random_bytes(size=len(object_name))
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertHeaders(resp, 'Object', 'PUT')

        # list container metadata
        resp, _ = self.container_client.list_container_metadata(
            self.container_name)
        self.assertHeaders(resp, 'Container', 'HEAD')

        self.assertIn('x-container-read', resp)
        self.assertEqual(resp['x-container-read'], '.r:*,.rlistings')

        # get auth token of alternative user
        alt_auth_data = self.object_client_alt.auth_provider.auth_data
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=alt_auth_data
        )
        # access object using alternate user creds
        resp, body = self.object_client.get_object(
            self.container_name, object_name)
        self.assertHeaders(resp, 'Object', 'GET')

        self.assertEqual(body, data)
