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
import six
import time
import zlib

from tempest.api.object_storage import base
from tempest.common import custom_matchers
from tempest.common.utils import data_utils
from tempest import test


class ObjectTest(base.BaseObjectTest):
    @classmethod
    def setUpClass(cls):
        super(ObjectTest, cls).setUpClass()
        cls.container_name = data_utils.rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)
        cls.containers = [cls.container_name]

    @classmethod
    def tearDownClass(cls):
        cls.delete_containers(cls.containers)
        super(ObjectTest, cls).tearDownClass()

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
            self.assertEqual(resp['status'], '201')

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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @test.attr(type='gate')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=None)
        self.assertIn('content-disposition', resp)
        self.assertEqual(resp['content-disposition'], 'inline')
        self.assertEqual(body, data)

    @test.attr(type='gate')
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
        self.assertEqual(resp['status'], '201')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @test.attr(type='gate')
    def test_create_object_with_expect_continue(self):
        # create object with expect_continue
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        metadata = {'Expect': '100-continue'}
        resp = self.custom_object_client.create_object_continue(
            self.container_name,
            object_name,
            data,
            metadata=metadata)

        self.assertIn('status', resp)
        self.assertEqual(resp['status'], '100')

        self.custom_object_client.create_object_continue(
            self.container_name,
            object_name,
            data,
            metadata=None)

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @test.attr(type='gate')
    def test_create_object_with_transfer_encoding(self):
        # create object with transfer_encoding
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string(1024)
        status, _, resp_headers = self.object_client.put_object_with_chunk(
            container=self.container_name,
            name=object_name,
            contents=StringIO.StringIO(data),
            chunk_size=512)
        self.assertEqual(status, 201)
        self.assertHeaders(resp_headers, 'Object', 'PUT')

        # check uploaded content
        _, body = self.object_client.get_object(self.container_name,
                                                object_name)
        self.assertEqual(data, body)

    @test.attr(type='gate')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)
        self.assertEqual(data, body)

    @test.attr(type='gate')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')
        self.assertEqual(data, body)

    @test.attr(type='gate')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], '')
        self.assertEqual(data, body)

    @test.attr(type='gate')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)
        self.assertEqual(data, body)

    @test.attr(type='gate')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)
        self.assertEqual(data, body)

    @test.attr(type='gate')
    def test_delete_object(self):
        # create object
        object_name = data_utils.rand_name(name='TestObject')
        data = data_utils.arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # delete object
        resp, _ = self.object_client.delete_object(self.container_name,
                                                   object_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'DELETE')

    @test.attr(type='smoke')
    def test_update_object_metadata(self):
        # update object metadata
        object_name, data = self._create_object()

        metadata = {'X-Object-Meta-test-meta': 'Meta'}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name,
            object_name,
            metadata,
            metadata_prefix='')
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')

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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta1', resp)

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta1', resp)
        self.assertIn('x-object-meta-test-meta2', resp)
        self.assertEqual(resp['x-object-meta-test-meta2'], 'Meta2')

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-manifest', resp)
        self.assertNotEqual(len(resp['x-object-manifest']), 0)

    def test_update_object_metadata_with_x_object_metakey(self):
        # update object metadata with a blenk value of metadata
        object_name, data = self._create_object()

        update_metadata = {'X-Object-Meta-test-meta': ''}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name,
            object_name,
            update_metadata,
            metadata_prefix='')
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], '')

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'POST')

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertNotIn('x-object-meta-test-meta', resp)

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'HEAD')
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')

    @test.attr(type='smoke')
    def test_list_no_object_metadata(self):
        # get empty list of object metadata
        object_name, data = self._create_object()

        resp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'HEAD')
        self.assertNotIn('x-object-meta-', str(resp))

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)

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
    def test_get_object(self):
        # retrieve object's data (in response body)

        # create object
        object_name, data = self._create_object()
        # get object
        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')

        self.assertEqual(body, data)

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertIn('x-object-meta-test-meta', resp)
        self.assertEqual(resp['x-object-meta-test-meta'], 'Meta')
        self.assertEqual(body, data)

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data[rand_num - 3: rand_num])

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)

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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @test.attr(type='smoke')
    def test_get_object_with_x_newest(self):
        # get object with x_newest
        object_name, data = self._create_object()

        list_metadata = {'X-Newest': 'true'}
        resp, body = self.object_client.get_object(
            self.container_name,
            object_name,
            metadata=list_metadata)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, data)

    @test.attr(type='smoke')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        # check data
        resp, body = self.object_client.get_object(self.container_name,
                                                   dst_object_name)
        self.assertEqual(body, src_data)

    @test.attr(type='smoke')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        # check the content type
        resp, _ = self.object_client.list_object_metadata(self.container_name,
                                                          object_name)
        self.assertEqual(resp['content-type'], metadata['content-type'])

    @test.attr(type='smoke')
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
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'COPY')
        self.assertEqual(
            resp['x-copied-from'],
            self.container_name + "/" + src_object_name)

        # check data
        self._check_copied_obj(dst_object_name, src_data)

    @test.attr(type='smoke')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'POST')

        # copy object from source container to destination container
        resp, _ = self.object_client.copy_object_across_containers(
            src_container_name, object_name, dst_container_name,
            object_name)
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        # check if object is present in destination container
        resp, body = self.object_client.get_object(dst_container_name,
                                                   object_name)
        self.assertEqual(body, data)
        actual_meta_key = 'x-object-meta-' + meta_key
        self.assertIn(actual_meta_key, resp)
        self.assertEqual(resp[actual_meta_key], meta_value)

    @test.attr(type='smoke')
    def test_copy_object_with_x_fresh_metadata(self):
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_object_name, data = self._create_object(metadata)

        # copy source object with x_fresh_metadata header
        metadata = {'X-Fresh-Metadata': 'true'}
        dst_object_name, resp = self._copy_object_2d(src_object_name,
                                                     metadata)

        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'COPY')

        self.assertNotIn('x-object-meta-src', resp)
        self.assertEqual(resp['x-copied-from'],
                         self.container_name + "/" + src_object_name)

        # check that destination object does NOT have any object-meta
        self._check_copied_obj(dst_object_name, data, not_in_meta=["src"])

    @test.attr(type='smoke')
    def test_copy_object_with_x_object_metakey(self):
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_obj_name, data = self._create_object(metadata)

        # copy source object to destination with x-object-meta-key
        metadata = {'x-object-meta-test': ''}
        dst_obj_name, resp = self._copy_object_2d(src_obj_name, metadata)

        self.assertEqual(resp['status'], '201')
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
    def test_copy_object_with_x_object_meta(self):
        # create source object
        metadata = {'x-object-meta-src': 'src_value'}
        src_obj_name, data = self._create_object(metadata)

        # copy source object to destination with object metadata
        metadata = {'x-object-meta-test': 'value'}
        dst_obj_name, resp = self._copy_object_2d(src_obj_name, metadata)

        self.assertEqual(resp['status'], '201')
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
            self.assertEqual(resp['status'], '201')
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
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Object', 'GET')


class PublicObjectTest(base.BaseObjectTest):
    def setUp(self):
        super(PublicObjectTest, self).setUp()
        self.container_name = data_utils.rand_name(name='TestContainer')
        self.container_client.create_container(self.container_name)

    def tearDown(self):
        self.delete_containers([self.container_name])
        super(PublicObjectTest, self).tearDown()

    @test.attr(type='smoke')
    def test_access_public_container_object_without_using_creds(self):
        # make container public-readable and access an object in it object
        # anonymously, without using credentials

        # update container metadata to make it publicly readable
        cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers, metadata_prefix='')
        self.assertIn(int(resp_meta['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'POST')

        # create object
        object_name = data_utils.rand_name(name='Object')
        data = data_utils.arbitrary_string(size=len(object_name),
                                           base_text=object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        # list container metadata
        resp_meta, _ = self.container_client.list_container_metadata(
            self.container_name)
        self.assertIn(int(resp_meta['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'HEAD')

        self.assertIn('x-container-read', resp_meta)
        self.assertEqual(resp_meta['x-container-read'], '.r:*,.rlistings')

        # trying to get object with empty headers as it is public readable
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=None
        )
        resp, body = self.custom_object_client.get_object(
            self.container_name, object_name)
        self.assertHeaders(resp, 'Object', 'GET')

        self.assertEqual(body, data)

    @test.attr(type='smoke')
    def test_access_public_object_with_another_user_creds(self):
        # make container public-readable and access an object in it using
        # another user's credentials
        cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers,
            metadata_prefix='')
        self.assertIn(int(resp_meta['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp_meta, 'Container', 'POST')

        # create object
        object_name = data_utils.rand_name(name='Object')
        data = data_utils.arbitrary_string(size=len(object_name) * 1,
                                           base_text=object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertEqual(resp['status'], '201')
        self.assertHeaders(resp, 'Object', 'PUT')

        # list container metadata
        resp, _ = self.container_client.list_container_metadata(
            self.container_name)
        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'HEAD')

        self.assertIn('x-container-read', resp)
        self.assertEqual(resp['x-container-read'], '.r:*,.rlistings')

        # get auth token of alternative user
        alt_auth_data = self.identity_client_alt.auth_provider.auth_data
        self.custom_object_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=alt_auth_data
        )
        # access object using alternate user creds
        resp, body = self.custom_object_client.get_object(
            self.container_name, object_name)
        self.assertHeaders(resp, 'Object', 'GET')

        self.assertEqual(body, data)
