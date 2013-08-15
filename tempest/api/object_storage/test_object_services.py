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

import hashlib
import time

from tempest.api.object_storage import base
from tempest.common.utils.data_utils import arbitrary_string
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr
from tempest.test import HTTP_SUCCESS


class ObjectTest(base.BaseObjectTest):
    @classmethod
    def setUpClass(cls):
        super(ObjectTest, cls).setUpClass()
        cls.container_name = rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)
        cls.containers = [cls.container_name]

        cls.data.setup_test_user()
        resp, body = cls.token_client.auth(cls.data.test_user,
                                           cls.data.test_password,
                                           cls.data.test_tenant)
        cls.new_token = cls.token_client.get_token(cls.data.test_user,
                                                   cls.data.test_password,
                                                   cls.data.test_tenant)
        cls.custom_headers = {'X-Auth-Token': cls.new_token}

    @classmethod
    def tearDownClass(cls):
        cls.delete_containers(cls.containers)
        # delete the user setup created
        cls.data.teardown_all()
        super(ObjectTest, cls).tearDownClass()

    @attr(type='smoke')
    def test_create_object(self):
        # create object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # create another object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertEqual(resp['status'], '201')

    @attr(type='smoke')
    def test_delete_object(self):
        # create object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # delete object
        resp, _ = self.object_client.delete_object(self.container_name,
                                                   object_name)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)

    @attr(type='smoke')
    def test_object_metadata(self):
        # add metadata to storage object, test if metadata is retrievable

        # create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # set object metadata
        meta_key = rand_name(name='test-')
        meta_value = rand_name(name='MetaValue-')
        orig_metadata = {meta_key: meta_value}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name, object_name, orig_metadata)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)

        # get object metadata
        resp, resp_metadata = self.object_client.list_object_metadata(
            self.container_name, object_name)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        actual_meta_key = 'x-object-meta-' + meta_key
        self.assertTrue(actual_meta_key in resp)
        self.assertEqual(resp[actual_meta_key], meta_value)

    @attr(type='smoke')
    def test_get_object(self):
        # retrieve object's data (in response body)

        # create object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # get object
        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.assertEqual(body, data)

    @attr(type='smoke')
    def test_copy_object_in_same_container(self):
        # create source object
        src_object_name = rand_name(name='SrcObject')
        src_data = arbitrary_string(size=len(src_object_name) * 2,
                                    base_text=src_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   src_object_name,
                                                   src_data)
        # create destination object
        dst_object_name = rand_name(name='DstObject')
        dst_data = arbitrary_string(size=len(dst_object_name) * 3,
                                    base_text=dst_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   dst_object_name,
                                                   dst_data)
        # copy source object to destination
        resp, _ = self.object_client.copy_object_in_same_container(
            self.container_name, src_object_name, dst_object_name)
        self.assertEqual(resp['status'], '201')
        # check data
        resp, body = self.object_client.get_object(self.container_name,
                                                   dst_object_name)
        self.assertEqual(body, src_data)

    @attr(type='smoke')
    def test_copy_object_to_itself(self):
        # change the content type of an existing object

        # create object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        self.object_client.create_object(self.container_name,
                                         object_name, data)
        # get the old content type
        resp_tmp, _ = self.object_client.list_object_metadata(
            self.container_name, object_name)
        # change the content type of the object
        metadata = {'content-type': 'text/plain; charset=UTF-8'}
        self.assertNotEqual(resp_tmp['content-type'], metadata['content-type'])
        resp, _ = self.object_client.copy_object_in_same_container(
            self.container_name, object_name, object_name, metadata)
        self.assertEqual(resp['status'], '201')
        # check the content type
        resp, _ = self.object_client.list_object_metadata(self.container_name,
                                                          object_name)
        self.assertEqual(resp['content-type'], metadata['content-type'])

    @attr(type='smoke')
    def test_copy_object_2d_way(self):
        # create source object
        src_object_name = rand_name(name='SrcObject')
        src_data = arbitrary_string(size=len(src_object_name) * 2,
                                    base_text=src_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   src_object_name, src_data)
        # create destination object
        dst_object_name = rand_name(name='DstObject')
        dst_data = arbitrary_string(size=len(dst_object_name) * 3,
                                    base_text=dst_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   dst_object_name, dst_data)
        # copy source object to destination
        resp, _ = self.object_client.copy_object_2d_way(self.container_name,
                                                        src_object_name,
                                                        dst_object_name)
        self.assertEqual(resp['status'], '201')
        # check data
        resp, body = self.object_client.get_object(self.container_name,
                                                   dst_object_name)
        self.assertEqual(body, src_data)

    @attr(type='smoke')
    def test_copy_object_across_containers(self):
        # create a container to use as  asource container
        src_container_name = rand_name(name='TestSourceContainer')
        self.container_client.create_container(src_container_name)
        self.containers.append(src_container_name)
        # create a container to use as a destination container
        dst_container_name = rand_name(name='TestDestinationContainer')
        self.container_client.create_container(dst_container_name)
        self.containers.append(dst_container_name)
        # create object in source container
        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name) * 2,
                                base_text=object_name)
        resp, _ = self.object_client.create_object(src_container_name,
                                                   object_name, data)
        # set object metadata
        meta_key = rand_name(name='test-')
        meta_value = rand_name(name='MetaValue-')
        orig_metadata = {meta_key: meta_value}
        resp, _ = self.object_client.update_object_metadata(src_container_name,
                                                            object_name,
                                                            orig_metadata)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        try:
            # copy object from source container to destination container
            resp, _ = self.object_client.copy_object_across_containers(
                src_container_name, object_name, dst_container_name,
                object_name)
            self.assertEqual(resp['status'], '201')

            # check if object is present in destination container
            resp, body = self.object_client.get_object(dst_container_name,
                                                       object_name)
            self.assertEqual(body, data)
            actual_meta_key = 'x-object-meta-' + meta_key
            self.assertTrue(actual_meta_key in resp)
            self.assertEqual(resp[actual_meta_key], meta_value)

        except Exception as e:
            self.fail("Got exception :%s ; while copying"
                      " object across containers" % e)

    @attr(type='gate')
    def test_get_object_using_temp_url(self):
        # access object using temporary URL within expiration time

        try:
            # update account metadata
            # flag to check if account metadata got updated
            flag = False
            key = 'Meta'
            metadata = {'Temp-URL-Key': key}
            resp, _ = self.account_client.create_account_metadata(
                metadata=metadata)
            self.assertIn(int(resp['status']), HTTP_SUCCESS)
            flag = True
            resp, _ = self.account_client.list_account_metadata()
            self.assertIn('x-account-meta-temp-url-key', resp)
            self.assertEqual(resp['x-account-meta-temp-url-key'], key)

            # create object
            object_name = rand_name(name='ObjectTemp')
            data = arbitrary_string(size=len(object_name),
                                    base_text=object_name)
            self.object_client.create_object(self.container_name,
                                             object_name, data)
            expires = int(time.time() + 10)

            # trying to get object using temp url with in expiry time
            _, body = self.object_client.get_object_using_temp_url(
                self.container_name, object_name,
                expires, key)
            self.assertEqual(body, data)
        finally:
            if flag:
                resp, _ = self.account_client.delete_account_metadata(
                    metadata=metadata)
                resp, _ = self.account_client.list_account_metadata()
                self.assertNotIn('x-account-meta-temp-url-key', resp)

    @attr(type='gate')
    def test_object_upload_in_segments(self):
        # create object
        object_name = rand_name(name='LObject')
        data = arbitrary_string()
        segments = 10
        data_segments = [data + str(i) for i in xrange(segments)]
        # uploading segments
        for i in xrange(segments):
            resp, _ = self.object_client.create_object_segments(
                self.container_name, object_name, i, data_segments[i])
            self.assertEqual(resp['status'], '201')
        # creating a manifest file
        metadata = {'X-Object-Manifest': '%s/%s/'
                    % (self.container_name, object_name)}
        self.object_client.create_object(self.container_name,
                                         object_name, data='')
        resp, _ = self.object_client.update_object_metadata(
            self.container_name, object_name, metadata, metadata_prefix='')
        resp, _ = self.object_client.list_object_metadata(
            self.container_name, object_name)
        self.assertIn('x-object-manifest', resp)
        self.assertEqual(resp['x-object-manifest'],
                         '%s/%s/' % (self.container_name, object_name))

        # downloading the object
        resp, body = self.object_client.get_object(
            self.container_name, object_name)
        self.assertEqual(''.join(data_segments), body)

    @attr(type='gate')
    def test_get_object_if_different(self):
        # http://en.wikipedia.org/wiki/HTTP_ETag
        # Make a conditional request for an object using the If-None-Match
        # header, it should get downloaded only if the local file is different,
        # otherwise the response code should be 304 Not Modified
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        self.object_client.create_object(self.container_name,
                                         object_name, data)
        # local copy is identical, no download
        md5 = hashlib.md5(data).hexdigest()
        headers = {'If-None-Match': md5}
        url = "%s/%s" % (self.container_name, object_name)
        resp, _ = self.object_client.get(url, headers=headers)
        self.assertEqual(resp['status'], '304')

        # local copy is different, download
        local_data = "something different"
        md5 = hashlib.md5(local_data).hexdigest()
        headers = {'If-None-Match': md5}
        resp, body = self.object_client.get(url, headers=headers)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)


class PublicObjectTest(base.BaseObjectTest):
    def setUp(self):
        super(PublicObjectTest, self).setUp()
        self.container_name = rand_name(name='TestContainer')
        self.container_client.create_container(self.container_name)

    def tearDown(self):
        self.delete_containers([self.container_name])
        super(PublicObjectTest, self).tearDown()

    @attr(type='smoke')
    def test_access_public_container_object_without_using_creds(self):
        # make container public-readable and access an object in it object
        # anonymously, without using credentials

        # update container metadata to make it publicly readable
        cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
        resp_meta, body = self.container_client.update_container_metadata(
            self.container_name, metadata=cont_headers, metadata_prefix='')
        self.assertIn(int(resp_meta['status']), HTTP_SUCCESS)
        # create object
        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name),
                                base_text=object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertEqual(resp['status'], '201')

        # list container metadata
        resp_meta, _ = self.container_client.list_container_metadata(
            self.container_name)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.assertIn('x-container-read', resp_meta)
        self.assertEqual(resp_meta['x-container-read'], '.r:*,.rlistings')

        # trying to get object with empty headers as it is public readable
        resp, body = self.custom_object_client.get_object(
            self.container_name, object_name, metadata={})
        self.assertEqual(body, data)

    @attr(type='smoke')
    def test_access_public_object_with_another_user_creds(self):
        # make container public-readable and access an object in it using
        # another user's credentials
        try:
            cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
            resp_meta, body = self.container_client.update_container_metadata(
                self.container_name, metadata=cont_headers,
                metadata_prefix='')
            self.assertIn(int(resp_meta['status']), HTTP_SUCCESS)
            # create object
            object_name = rand_name(name='Object')
            data = arbitrary_string(size=len(object_name) * 1,
                                    base_text=object_name)
            resp, _ = self.object_client.create_object(self.container_name,
                                                       object_name, data)
            self.assertEqual(resp['status'], '201')

            # list container metadata
            resp, _ = self.container_client.list_container_metadata(
                self.container_name)
            self.assertIn(int(resp['status']), HTTP_SUCCESS)
            self.assertIn('x-container-read', resp)
            self.assertEqual(resp['x-container-read'], '.r:*,.rlistings')

            # get auth token of alternative user
            token = self.identity_client_alt.get_auth()
            headers = {'X-Auth-Token': token}
            # access object using alternate user creds
            resp, body = self.custom_object_client.get_object(
                self.container_name, object_name,
                metadata=headers)
            self.assertEqual(body, data)

        except Exception as e:
            self.fail("Failed to get public readable object with another"
                      " user creds raised exception is %s" % e)
