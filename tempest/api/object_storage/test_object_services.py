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

import cStringIO as StringIO
import hashlib
import random
import re
import time
import zlib

import six
from tempest_lib.common.utils import data_utils

from tempest.api.object_storage import base
from tempest import clients
from tempest.common import custom_matchers
from tempest import config
from tempest import test

CONF = config.CONF


class ObjectTest(base.BaseObjectTest):

    @classmethod
    def resource_setup(cls):
        super(ObjectTest, cls).resource_setup()
        cls.container_name = data_utils.rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)
        cls.containers = [cls.container_name]

    @classmethod
    def resource_cleanup(cls):
        cls.delete_containers(cls.containers)
        super(ObjectTest, cls).resource_cleanup()

    def _create_object(self, metadata=None):
        # setup object
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        self.object_client.create_object(self.container_name,
                                         object_name, data, metadata=metadata)

        return object_name, data

    def _upload_segments(self):
        # create object
        object_name = data_utils.rand_name(name='LObject')
        data = data_utils.arbitrary_string()
        segments = 10
        data_segments = [data + str(i) for i in six.moves.xrange(segments)]
        # uploading segments
        for i in six.moves.xrange(segments):
            resp, _ = self.object_client.create_object_segments(
                self.container_name, object_name, i, data_segments[i])

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

    @test.attr(type='gate')
    @test.idempotent_id('5b4ce26f-3545-46c9-a2ba-5754358a4c62')
    def test_create_object(self):
        # create object
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # create another object
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @test.attr(type='gate')
    @test.idempotent_id('5daebb1d-f0d5-4dc9-b541-69672eff00b0')
    def test_create_object_with_content_disposition(self):
        # create object with content_disposition
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.attr(type='gate')
    @test.idempotent_id('605f8317-f945-4bee-ae91-013f1da8f0a0')
    def test_create_object_with_content_encoding(self):
        # create object with content_encoding
        object_name = data_utils.rand_name(name='TestObject')

        # put compressed string
        data_before = 'x' * 2000
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

    @test.attr(type='gate')
    @test.idempotent_id('73820093-0503-40b1-a478-edf0e69c7d1f')
    def test_create_object_with_etag(self):
        # create object with etag
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        md5 = hashlib.md5(data).hexdigest()
        metadata = {'Etag': md5}
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

    @test.attr(type='gate')
    @test.idempotent_id('84dafe57-9666-4f6d-84c8-0814d37923b8')
    def test_create_object_with_expect_continue(self):
        # create object with expect_continue
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        metadata = {'Expect': '100-continue'}
        resp = self.object_client.create_object_continue(
            self.container_name,
            object_name,
            data,
            metadata=metadata)

        self.assertIn('status', resp)
        self.assertEqual(resp['status'], '100')

        self.object_client.create_object_continue(
            self.container_name,
            object_name,
            data,
            metadata=None)

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @test.attr(type='gate')
    @test.idempotent_id('4f84422a-e2f2-4403-b601-726a4220b54e')
    def test_create_object_with_transfer_encoding(self):
        # create object with transfer_encoding
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string(1024)
        status, _, resp_headers = self.object_client.put_object_with_chunk(
            container=self.container_name,
            name=object_name,
            contents=StringIO.StringIO(data),
            chunk_size=512)
        self.assertHeaders(resp_headers, 'Object', 'PUT')

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @test.attr(type='gate')
    @test.idempotent_id('0f3d62a6-47e3-4554-b0e5-1a5dc372d501')
    def test_create_object_with_x_fresh_metadata(self):
        # create object with x_fresh_metadata
        object_name_base = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.attr(type='gate')
    @test.idempotent_id('1c7ed3e4-2099-406b-b843-5301d4811baf')
    def test_create_object_with_x_object_meta(self):
        # create object with object_meta
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.attr(type='gate')
    @test.idempotent_id('e4183917-33db-4153-85cc-4dacbb938865')
    def test_create_object_with_x_object_metakey(self):
        # create object with the blank value of metadata
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.attr(type='gate')
    @test.idempotent_id('ce798afc-b278-45de-a5ce-2ea124b98b99')
    def test_create_object_with_x_remove_object_meta(self):
        # create object with x_remove_object_meta
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.attr(type='gate')
    @test.idempotent_id('ad21e342-7916-4f9e-ab62-a1f885f2aaf9')
    def test_create_object_with_x_remove_object_metakey(self):
        # create object with the blank value of remove metadata
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.attr(type='gate')
    @test.idempotent_id('17738d45-03bd-4d45-9e0b-7b2f58f98687')
    def test_delete_object(self):
        # create object
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # delete object
        resp, _ = self.object_client.delete_object(self.container_name,
                                                   object_name)
        self.assertHeaders(resp, 'Object', 'DELETE')

    @test.attr(type='smoke')
    @test.idempotent_id('7a94c25d-66e6-434c-9c38-97d4e2c29945')
    def test_update_object_metadata(self):
        # update object metadata
        object_name, data = self._create_object()

        metadata = {'X-Object-Meta-test-meta': 'Meta'}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name,
            object_name,
            metadata,
            metadata_prefix='')
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')

    @test.idempotent_id('48650ed0-c189-4e1e-ad6b-1d4770c6e134')
    def test_update_object_metadata_with_remove_metadata(self):
        # update object metadata with remove metadata
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        create_metadata = {'X-Object-Meta-test-meta1': 'Meta1'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        update_metadata = {'X-Remove-Object-Meta-test-meta1': 'Meta1'}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name,
            object_name,
            update_metadata,
            metadata_prefix='')
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta1', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('f726174b-2ded-4708-bff7-729d12ce1f84')
    def test_update_object_metadata_with_create_and_remove_metadata(self):
        # creation and deletion of metadata with one request
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        create_metadata = {'X-Object-Meta-test-meta1': 'Meta1'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        update_metadata = {'X-Object-Meta-test-meta2': 'Meta2',
                           'X-Remove-Object-Meta-test-meta1': 'Meta1'}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name,
            object_name,
            update_metadata,
            metadata_prefix='')
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta1', resp)
        self.assertIn('x-object-meta-test-meta2', resp)
        self.assertEqual(resp['x-object-meta-test-meta2'], 'Meta2')

    @test.attr(type='smoke')
    @test.idempotent_id('08854588-6449-4bb7-8cca-f2e1040f5e6f')
    def test_update_object_metadata_with_x_object_manifest(self):
        # update object metadata with x_object_manifest

        # uploading segments
        object_name, data_segments = self._upload_segments()
        # creating a manifest file
        data_empty = ''
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data_empty,
                                         metadata=None)
        object_prefix = '%s/%s' % (self.container_name, object_name)
        update_metadata = {'X-Object-Manifest': object_prefix}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name,
            object_name,
            update_metadata,
            metadata_prefix='')
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-manifest', resp)
        self.assertNotEqual(len(resp['x-object-manifest']), 0)

    @test.idempotent_id('0dbbe89c-6811-4d84-a2df-eca2bdd40c0e')
    def test_update_object_metadata_with_x_object_metakey(self):
        # update object metadata with a blenk value of metadata
        object_name, data = self._create_object()

        update_metadata = {'X-Object-Meta-test-meta': ''}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name,
            object_name,
            update_metadata,
            metadata_prefix='')
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], '')

    @test.attr(type='smoke')
    @test.idempotent_id('9a88dca4-b684-425b-806f-306cd0e57e42')
    def test_update_object_metadata_with_x_remove_object_metakey(self):
        # update object metadata with a blank value of remove metadata
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        create_metadata = {'X-Object-Meta-test-meta': 'Meta'}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        update_metadata = {'X-Remove-Object-Meta-test-meta': ''}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name,
            object_name,
            update_metadata,
            metadata_prefix='')
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)

    @test.attr(type='smoke')
    @test.idempotent_id('9a447cf6-de06-48de-8226-a8c6ed31caf2')
    def test_list_object_metadata(self):
        # get object metadata
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.attr(type='smoke')
    @test.idempotent_id('170fb90e-f5c3-4b1f-ae1b-a18810821172')
    def test_list_no_object_metadata(self):
        # get empty list of object metadata
        object_name, data = self._create_object()

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertHeaders(resp, 'Object', 'HEAD')
        self.assertNotIn('x-object-meta-', str(resp))

    @test.attr(type='smoke')
    @test.idempotent_id('23a3674c-d6de-46c3-86af-ff92bfc8a3da')
    def test_list_object_metadata_with_x_object_manifest(self):
        # get object metadata with x_object_manifest

        # uploading segments
        object_name, data_segments = self._upload_segments()
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
        self.assertTrue(re.match("^\d+\.?\d*\Z", resp['x-timestamp']))
        self.assertNotEqual(len(resp['content-type']), 0)
        self.assertTrue(re.match("^tx[0-9a-f]*-[0-9a-f]*$",
                                 resp['x-trans-id']))
        self.assertNotEqual(len(resp['date']), 0)
        self.assertEqual(resp['accept-ranges'], 'bytes')
        self.assertEqual(resp['x-object-manifest'],
                         '%s/%s' % (self.container_name, object_name))

    @test.attr(type='smoke')
    @test.idempotent_id('02610ba7-86b7-4272-9ed8-aa8d417cb3cd')
    def test_get_object(self):
        # retrieve object's data (in response body)

        # create object
        object_name, data = self._create_object()
        # get object
        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertHeaders(resp, 'Object', 'GET')

        self.assertEqual(body, data)

    @test.attr(type='smoke')
    @test.idempotent_id('005f9bf6-e06d-41ec-968e-96c78e0b1d82')
    def test_get_object_with_metadata(self):
        # get object with metadata
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.attr(type='smoke')
    @test.idempotent_id('05a1890e-7db9-4a6c-90a8-ce998a2bddfa')
    def test_get_object_with_range(self):
        # get object with range
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string(100)
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

    @test.attr(type='smoke')
    @test.idempotent_id('11b4515b-7ba7-4ca8-8838-357ded86fc10')
    def test_get_object_with_x_object_manifest(self):
        # get object with x_object_manifest

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
        self.assertTrue(re.match("^\d+\.?\d*\Z", resp['x-timestamp']))
        self.assertNotEqual(len(resp['content-type']), 0)
        self.assertTrue(re.match("^tx[0-9a-f]*-[0-9a-f]*$",
                                 resp['x-trans-id']))
        self.assertNotEqual(len(resp['date']), 0)
        self.assertEqual(resp['accept-ranges'], 'bytes')
        self.assertEqual(resp['x-object-manifest'],
                         '%s/%s' % (self.container_name, object_name))

        self.assertEqual(''.join(data_segments), body)

    @test.attr(type='smoke')
    @test.idempotent_id('c05b4013-e4de-47af-be84-e598062b16fc')
    def test_get_object_with_if_match(self):
        # get object with if_match
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string(10)
        create_md5 = hashlib.md5(data).hexdigest()
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

    @test.attr(type='smoke')
    @test.idempotent_id('be133639-e5d2-4313-9b1f-2d59fc054a16')
    def test_get_object_with_if_modified_since(self):
        # get object with if_modified_since
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
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

    @test.idempotent_id('641500d5-1612-4042-a04d-01fc4528bc30')
    def test_get_object_with_if_none_match(self):
        # get object with if_none_match
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string(10)
        create_md5 = hashlib.md5(data).hexdigest()
        create_metadata = {'Etag': create_md5}
        self.object_client.create_object(self.container_name,
                                         object_name,
                                         data,
                                         metadata=create_metadata)

        list_data = data_utils.arbitrary_string(15)
        list_md5 = hashlib.md5(list_data).hexdigest()
        list_metadata = {'If-None-Match': list_md5}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @test.attr(type='smoke')
    @test.idempotent_id('0aa1201c-10aa-467a-bee7-63cbdd463152')
    def test_get_object_with_if_unmodified_since(self):
        # get object with if_unmodified_since
        object_name, data = self._create_object()

        time_now = time.time()
        http_date = time.ctime(time_now + 86400)
        list_metadata = {'If-Unmodified-Since': http_date}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @test.attr(type='smoke')
    @test.idempotent_id('94587078-475f-48f9-a40f-389c246e31cd')
    def test_get_object_with_x_newest(self):
        # get object with x_newest
        object_name, data = self._create_object()

        list_metadata = {'X-Newest': 'true'}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @test.attr(type='smoke')
    @test.idempotent_id('1a9ab572-1b66-4981-8c21-416e2a5e6011')
    def test_copy_object_in_same_container(self):
        # create source object
        src_object_name = data_utils.rand_name(name='SrcObject')
        src_data = data_utils.arbitrary_string(size=len(src_object_name) * 2,
                                               base_text=src_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   src_object_name,
                                                   src_data)
        # create destination object
        dst_object_name = data_utils.rand_name(name='DstObject')
        dst_data = data_utils.arbitrary_string(size=len(dst_object_name) * 3,
                                               base_text=dst_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   dst_object_name,
                                                   dst_data)
        # copy source object to destination
        resp, _ = self.object_client.copy_object_in_same_container(
            self.container_name, src_object_name, dst_object_name)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check data
        resp, body = self.object_client.get_object(self.container_name,
                                                   dst_object_name)
        self.assertEqual(body, src_data)

    @test.attr(type='smoke')
    @test.idempotent_id('2248abba-415d-410b-9c30-22dff9cd6e67')
    def test_copy_object_to_itself(self):
        # change the content type of an existing object

        # create object
        object_name, data = self._create_object()
        # get the old content type
        resp_tmp, _ = self.object_client.list_object_metadata(
            self.container_name, object_name)
        # change the content type of the object
        metadata = {'content-type': 'text/plain; charset=UTF-8'}
        self.assertNotEqual(resp_tmp['content-type'], metadata['content-type'])
        resp, _ = self.object_client.copy_object_in_same_container(
            self.container_name, object_name, object_name, metadata)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check the content type
        resp, _ = self.object_client.list_object_metadata(self.container_name,
                                                          object_name)
        self.assertEqual(resp['content-type'], metadata['content-type'])

    @test.attr(type='smoke')
    @test.idempotent_id('06f90388-2d0e-40aa-934c-e9a8833e958a')
    def test_copy_object_2d_way(self):
        # create source object
        src_object_name = data_utils.rand_name(name='SrcObject')
        src_data = data_utils.arbitrary_string(size=len(src_object_name) * 2,
                                               base_text=src_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   src_object_name, src_data)
        # create destination object
        dst_object_name = data_utils.rand_name(name='DstObject')
        dst_data = data_utils.arbitrary_string(size=len(dst_object_name) * 3,
                                               base_text=dst_object_name)
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

    @test.attr(type='smoke')
    @test.idempotent_id('aa467252-44f3-472a-b5ae-5b57c3c9c147')
    def test_copy_object_across_containers(self):
        # create a container to use as  asource container
        src_container_name = data_utils.rand_name(name='TestSourceContainer')
        self.container_client.create_container(src_container_name)
        self.containers.append(src_container_name)
        # create a container to use as a destination container
        dst_container_name = data_utils.rand_name(
            name='TestDestinationContainer')
        self.container_client.create_container(dst_container_name)
        self.containers.append(dst_container_name)
        # create object in source container
        object_name = data_utils.rand_name(name='Object')
        data = data_utils.arbitrary_string(size=len(object_name) * 2,
                                           base_text=object_name)
        resp, _ = self.object_client.create_object(src_container_name,
                                                   object_name, data)
        # set object metadata
        meta_key = data_utils.rand_name(name='test-')
        meta_value = data_utils.rand_name(name='MetaValue-')
        orig_metadata = {meta_key: meta_value}
        resp, _ = self.object_client.update_object_metadata(src_container_name,
                                                            object_name,
                                                            orig_metadata)
        self.assertHeaders(resp, 'Object', 'POST')

        # copy object from source container to destination container
        resp, _ = self.object_client.copy_object_across_containers(
            src_container_name, object_name, dst_container_name,
            object_name)
        self.assertHeaders(resp, 'Object', 'PUT')

        # check if object is present in destination container
        resp, body = self.object_client.get_object(dst_container_name,
                                                   object_name)
        self.assertEqual(body, data)
        actual_meta_key = 'x-object-meta-' + meta_key
        self.assertIn(actual_meta_key, resp)
        self.assertEqual(resp[actual_meta_key], meta_value)

    @test.attr(type='smoke')
    @test.idempotent_id('5a9e2cc6-85b6-46fc-916d-0cbb7a88e5fd')
    def test_copy_object_with_x_fresh_metadata(self):
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_object_name, data = self._create_object(metadata)

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

    @test.attr(type='smoke')
    @test.idempotent_id('a28a8b99-e701-4d7e-9d84-3b66f121460b')
    def test_copy_object_with_x_object_metakey(self):
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_obj_name, data = self._create_object(metadata)

        # copy source object to destination with x-object-meta-key
        metadata = {'x-object-meta-test': ''}
        dst_obj_name, resp = self._copy_object_2d(src_obj_name, metadata)

        self.assertHeaders(resp, 'Object', 'COPY')

        expected = {'x-object-meta-test': '',
                    'x-object-meta-src': 'src_value',
                    'x-copied-from': self.container_name + "/" + src_obj_name}
        for key, value in six.iteritems(expected):
            self.assertIn(key, resp)
            self.assertEqual(value, resp[key])

        # check destination object
        self._check_copied_obj(dst_obj_name, data, in_meta=["test", "src"])

    @test.attr(type='smoke')
    @test.idempotent_id('edabedca-24c3-4322-9b70-d6d9f942a074')
    def test_copy_object_with_x_object_meta(self):
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_obj_name, data = self._create_object(metadata)

        # copy source object to destination with object metadata
        metadata = {'x-object-meta-test': 'value'}
        dst_obj_name, resp = self._copy_object_2d(src_obj_name, metadata)

        self.assertHeaders(resp, 'Object', 'COPY')

        expected = {'x-object-meta-test': 'value',
                    'x-object-meta-src': 'src_value',
                    'x-copied-from': self.container_name + "/" + src_obj_name}
        for key, value in six.iteritems(expected):
            self.assertIn(key, resp)
            self.assertEqual(value, resp[key])

        # check destination object
        self._check_copied_obj(dst_obj_name, data, in_meta=["test", "src"])

    @test.attr(type='gate')
    @test.idempotent_id('e3e6a64a-9f50-4955-b987-6ce6767c97fb')
    def test_object_upload_in_segments(self):
        # create object
        object_name = data_utils.rand_name(name='LObject')
        data = data_utils.arbitrary_string()
        segments = 10
        data_segments = [data + str(i) for i in six.moves.xrange(segments)]
        # uploading segments
        for i in six.moves.xrange(segments):
            resp, _ = self.object_client.create_object_segments(
                self.container_name, object_name, i, data_segments[i])
        # creating a manifest file
        metadata = {'X-Object-Manifest': '%s/%s/'
                    % (self.container_name, object_name)}
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data='')
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, _ = self.object_client.update_object_metadata(
            self.container_name, object_name, metadata, metadata_prefix='')
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
        self.assertEqual(''.join(data_segments), body)

    @test.attr(type='gate')
    @test.idempotent_id('50d01f12-526f-4360-9ac2-75dd508d7b68')
    def test_get_object_if_different(self):
        # http://en.wikipedia.org/wiki/HTTP_ETag
        # Make a conditional request for an object using the If-None-Match
        # header, it should get downloaded only if the local file is different,
        # otherwise the response code should be 304 Not Modified
        object_name, data = self._create_object()
        # local copy is identical, no download
        md5 = hashlib.md5(data).hexdigest()
        headers = {'If-None-Match': md5}
        url = "%s/%s" % (self.container_name, object_name)
        resp, _ = self.object_client.get(url, headers=headers)
        self.assertEqual(resp['status'], '304')

        # When the file is not downloaded from Swift server, response does
        # not contain 'X-Timestamp' header. This is the special case, therefore
        # the existence of response headers is checked without custom matcher.
        self.assertIn('content-type', resp)
        self.assertIn('x-trans-id', resp)
        self.assertIn('date', resp)
        self.assertIn('accept-ranges', resp)
        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

        # local copy is different, download
        local_data = "something different"
        md5 = hashlib.md5(local_data).hexdigest()
        headers = {'If-None-Match': md5}
        resp, body = self.object_client.get(url, headers=headers)
        self.assertHeaders(resp, 'Object', 'GET')


class PublicObjectTest(base.BaseObjectTest):

    @classmethod
    def setup_credentials(cls):
        super(PublicObjectTest, cls).setup_credentials()
        cls.os_alt = clients.Manager(
            cls.isolated_creds.get_creds_by_roles(
                roles=[CONF.object_storage.operator_role], force_new=True))

    @classmethod
    def setup_clients(cls):
        super(PublicObjectTest, cls).setup_clients()
        cls.identity_client_alt = cls.os_alt.identity_client

    def setUp(self):
        super(PublicObjectTest, self).setUp()
        self.container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.create_container(self.container_name)

    def tearDown(self):
        self.delete_containers([self.container_name])
        super(PublicObjectTest, self).tearDown()

    @test.attr(type='smoke')
    @test.idempotent_id('07c9cf95-c0d4-4b49-b9c8-0ef2c9b27193')
    def test_access_public_container_object_without_using_creds(self):
        # make container public-readable and access an object in it object
        # anonymously, without using credentials

        # update container metadata to make it publicly readable
        cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers, metadata_prefix='')
        self.assertHeaders(resp_meta, 'Container', 'POST')

        # create object
        object_name = data_utils.rand_name(name='Object')
        data = data_utils.arbitrary_string(size=len(object_name),
                                           base_text=object_name)
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

    @test.attr(type='smoke')
    @test.idempotent_id('54e2a2fe-42dc-491b-8270-8e4217dd4cdc')
    def test_access_public_object_with_another_user_creds(self):
        # make container public-readable and access an object in it using
        # another user's credentials
        cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertHeaders(resp_meta, 'Container', 'POST')

        # create object
        object_name = data_utils.rand_name(name='Object')
        data = data_utils.arbitrary_string(size=len(object_name) * 1,
                                           base_text=object_name)
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
        alt_auth_data = self.identity_client_alt.auth_provider.auth_data
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=alt_auth_data
        )
        # access object using alternate user creds
        resp, body = self.object_client.get_object(
            self.container_name, object_name)
        self.assertHeaders(resp, 'Object', 'GET')

        self.assertEqual(body, data)
