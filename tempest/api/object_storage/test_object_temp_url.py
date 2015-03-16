# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import hashlib
import hmac
import time
import urlparse

from tempest_lib.common.utils import data_utils

from tempest.api.object_storage import base
from tempest import config
from tempest import test

CONF = config.CONF


class ObjectTempUrlTest(base.BaseObjectTest):

    @classmethod
    def resource_setup(cls):
        super(ObjectTempUrlTest, cls).resource_setup()
        # create a container
        cls.container_name = data_utils.rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)
        cls.containers = [cls.container_name]

        # update account metadata
        cls.key = 'Meta'
        cls.metadatas = []
        metadata = {'Temp-URL-Key': cls.key}
        cls.metadatas.append(metadata)
        cls.account_client.create_account_metadata(metadata=metadata)

        # create an object
        cls.object_name = data_utils.rand_name(name='ObjectTemp')
        cls.content = data_utils.arbitrary_string(size=len(cls.object_name),
                                                  base_text=cls.object_name)
        cls.object_client.create_object(cls.container_name,
                                        cls.object_name, cls.content)

    @classmethod
    def resource_cleanup(cls):
        for metadata in cls.metadatas:
            cls.account_client.delete_account_metadata(
                metadata=metadata)

        cls.delete_containers(cls.containers)

        super(ObjectTempUrlTest, cls).resource_cleanup()

    def setUp(self):
        super(ObjectTempUrlTest, self).setUp()

        # make sure the metadata has been set
        account_client_metadata, _ = \
            self.account_client.list_account_metadata()
        self.assertIn('x-account-meta-temp-url-key',
                      account_client_metadata)
        self.assertEqual(
            account_client_metadata['x-account-meta-temp-url-key'],
            self.key)

    def _get_expiry_date(self, expiration_time=1000):
        return int(time.time() + expiration_time)

    def _get_temp_url(self, container, object_name, method, expires,
                      key):
        """Create the temporary URL."""

        path = "%s/%s/%s" % (
            urlparse.urlparse(self.object_client.base_url).path,
            container, object_name)

        hmac_body = '%s\n%s\n%s' % (method, expires, path)
        sig = hmac.new(key, hmac_body, hashlib.sha1).hexdigest()

        url = "%s/%s?temp_url_sig=%s&temp_url_expires=%s" % (container,
                                                             object_name,
                                                             sig, expires)

        return url

    @test.attr(type='gate')
    @test.idempotent_id('f91c96d4-1230-4bba-8eb9-84476d18d991')
    @test.requires_ext(extension='tempurl', service='object')
    def test_get_object_using_temp_url(self):
        expires = self._get_expiry_date()

        # get a temp URL for the created object
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "GET",
                                 expires, self.key)

        # trying to get object using temp url within expiry time
        resp, body = self.object_client.get(url)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, self.content)

        # Testing a HEAD on this Temp URL
        resp, body = self.object_client.head(url)
        self.assertHeaders(resp, 'Object', 'HEAD')

    @test.attr(type='gate')
    @test.idempotent_id('671f9583-86bd-4128-a034-be282a68c5d8')
    @test.requires_ext(extension='tempurl', service='object')
    def test_get_object_using_temp_url_key_2(self):
        key2 = 'Meta2-'
        metadata = {'Temp-URL-Key-2': key2}
        self.account_client.create_account_metadata(metadata=metadata)
        self.metadatas.append(metadata)

        # make sure the metadata has been set
        account_client_metadata, _ = \
            self.account_client.list_account_metadata()
        self.assertIn('x-account-meta-temp-url-key-2',
                      account_client_metadata)
        self.assertEqual(
            account_client_metadata['x-account-meta-temp-url-key-2'],
            key2)

        expires = self._get_expiry_date()
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "GET",
                                 expires, key2)
        resp, body = self.object_client.get(url)
        self.assertEqual(body, self.content)

    @test.attr(type='gate')
    @test.idempotent_id('9b08dade-3571-4152-8a4f-a4f2a873a735')
    @test.requires_ext(extension='tempurl', service='object')
    def test_put_object_using_temp_url(self):
        new_data = data_utils.arbitrary_string(
            size=len(self.object_name),
            base_text=data_utils.rand_name(name="random"))

        expires = self._get_expiry_date()
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "PUT",
                                 expires, self.key)

        # trying to put random data in the object using temp url
        resp, body = self.object_client.put(url, new_data, None)
        self.assertHeaders(resp, 'Object', 'PUT')

        # Testing a HEAD on this Temp URL
        resp, body = self.object_client.head(url)
        self.assertHeaders(resp, 'Object', 'HEAD')

        # Validate that the content of the object has been modified
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "GET",
                                 expires, self.key)

        _, body = self.object_client.get(url)
        self.assertEqual(body, new_data)

    @test.attr(type='gate')
    @test.idempotent_id('249a0111-5ad3-4534-86a7-1993d55f9185')
    @test.requires_ext(extension='tempurl', service='object')
    def test_head_object_using_temp_url(self):
        expires = self._get_expiry_date()

        # get a temp URL for the created object
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "HEAD",
                                 expires, self.key)

        # Testing a HEAD on this Temp URL
        resp, body = self.object_client.head(url)
        self.assertHeaders(resp, 'Object', 'HEAD')

    @test.attr(type='gate')
    @test.idempotent_id('9d9cfd90-708b-465d-802c-e4a8090b823d')
    @test.requires_ext(extension='tempurl', service='object')
    def test_get_object_using_temp_url_with_inline_query_parameter(self):
        expires = self._get_expiry_date()

        # get a temp URL for the created object
        url = self._get_temp_url(self.container_name, self.object_name, "GET",
                                 expires, self.key)
        url = url + '&inline'

        # trying to get object using temp url within expiry time
        resp, body = self.object_client.get(url)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertEqual(body, self.content)
        self.assertEqual(resp['content-disposition'], 'inline')
