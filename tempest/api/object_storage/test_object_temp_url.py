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
from urllib import parse as urlparse

from tempest.api.object_storage import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ObjectTempUrlTest(base.BaseObjectTest):
    """Test object temp url"""

    @classmethod
    def resource_setup(cls):
        super(ObjectTempUrlTest, cls).resource_setup()
        # create a container
        cls.container_name = cls.create_container()

        # update account metadata
        cls.key = 'Meta'
        cls.metadatas = []
        metadata = {'Temp-URL-Key': cls.key}
        cls.metadatas.append(metadata)
        cls.account_client.create_update_or_delete_account_metadata(
            create_update_metadata=metadata)

        # create an object
        cls.object_name, cls.content = cls.create_object(cls.container_name)

    @classmethod
    def resource_cleanup(cls):
        for metadata in cls.metadatas:
            cls.account_client.create_update_or_delete_account_metadata(
                delete_metadata=metadata)

        cls.delete_containers()

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
        hlib = getattr(
            hashlib,
            CONF.object_storage_feature_enabled.tempurl_digest_hashlib)
        sig = hmac.new(
            key.encode(), hmac_body.encode(), hlib
        ).hexdigest()

        url = "%s/%s?temp_url_sig=%s&temp_url_expires=%s" % (container,
                                                             object_name,
                                                             sig, expires)

        return url

    @decorators.idempotent_id('f91c96d4-1230-4bba-8eb9-84476d18d991')
    @utils.requires_ext(extension='tempurl', service='object')
    def test_get_object_using_temp_url(self):
        """Test getting object using temp url"""
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
        resp, _ = self.object_client.head(url)
        self.assertHeaders(resp, 'Object', 'HEAD')

    @decorators.idempotent_id('671f9583-86bd-4128-a034-be282a68c5d8')
    @utils.requires_ext(extension='tempurl', service='object')
    def test_get_object_using_temp_url_key_2(self):
        """Test getting object using metadata 'Temp-URL-Key-2'"""
        key2 = 'Meta2-'
        metadata = {'Temp-URL-Key-2': key2}
        self.account_client.create_update_or_delete_account_metadata(
            create_update_metadata=metadata)
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
        _, body = self.object_client.get(url)
        self.assertEqual(body, self.content)

    @decorators.idempotent_id('9b08dade-3571-4152-8a4f-a4f2a873a735')
    @utils.requires_ext(extension='tempurl', service='object')
    def test_put_object_using_temp_url(self):
        """Test putting object using temp url"""
        new_data = data_utils.random_bytes(size=len(self.object_name))

        expires = self._get_expiry_date()
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "PUT",
                                 expires, self.key)

        # trying to put random data in the object using temp url
        resp, _ = self.object_client.put(url, new_data, None)
        self.assertHeaders(resp, 'Object', 'PUT')

        # Testing a HEAD on this Temp URL
        resp, _ = self.object_client.head(url)
        self.assertHeaders(resp, 'Object', 'HEAD')

        # Validate that the content of the object has been modified
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "GET",
                                 expires, self.key)

        _, body = self.object_client.get(url)
        self.assertEqual(body, new_data)

    @decorators.idempotent_id('249a0111-5ad3-4534-86a7-1993d55f9185')
    @utils.requires_ext(extension='tempurl', service='object')
    def test_head_object_using_temp_url(self):
        """Test HEAD operation of object using temp url"""
        expires = self._get_expiry_date()

        # get a temp URL for the created object
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "HEAD",
                                 expires, self.key)

        # Testing a HEAD on this Temp URL
        resp, _ = self.object_client.head(url)
        self.assertHeaders(resp, 'Object', 'HEAD')

    @decorators.idempotent_id('9d9cfd90-708b-465d-802c-e4a8090b823d')
    @utils.requires_ext(extension='tempurl', service='object')
    def test_get_object_using_temp_url_with_inline_query_parameter(self):
        """Test getting object using temp url with inline query parameter"""
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

    @decorators.idempotent_id('a4c34c55-1268-4efd-a9e3-17d8ef1e5b2c')
    @utils.requires_ext(extension='tempurl', service='object')
    def test_get_object_using_temp_url_with_prefix(self):
        """Test TempURL access for objects using a prefix in the container.

        Ensures that an object with a prefix in its name can be accessed
        via a TempURL using the prefix parameter.
        """

        # Set TempURL key for container
        tempurl_key = data_utils.rand_name("tempurlkey")
        metadata = {'Temp-URL-Key': tempurl_key}
        self.container_client.create_update_or_delete_container_metadata(
            self.container_name,
            create_update_metadata=metadata,
        )

        # Create object WITH prefix
        prefix = "public"
        object_name = f"{prefix}/tempurl_test.txt"
        object_data = data_utils.arbitrary_string()
        self.object_client.create_object(
            self.container_name, object_name, object_data
        )

        # Compute prefix-based TempURL signature
        expires = int(time.time()) + 300
        account = self.account_client.base_url.rstrip("/").split("/")[-1]
        path = f"/v1/{account}/{self.container_name}/{prefix}"
        hmac_body = f"GET\n{expires}\nprefix:{path}"
        hlib = getattr(
            hashlib, CONF.object_storage_feature_enabled.tempurl_digest_hashlib
        )
        sig = hmac.new(
            tempurl_key.encode(),
            hmac_body.encode(),
            hlib
        ).hexdigest()

        # Construct TempURL with prefix parameter
        base_url = self.object_client.base_url.rstrip("/")
        tempurl = (
            f"{base_url}/{self.container_name}/{object_name}"
            f"?temp_url_sig={sig}&temp_url_expires={expires}"
            f"&temp_url_prefix={prefix}"
        )

        # Clear auth to mimic public TempURL access
        self.object_client.auth_provider.set_alt_auth_data(
            request_part='headers', auth_data=None
        )

        # Construct relative URL and request
        relative_url = tempurl.replace(base_url + "/", "")
        resp, body = self.object_client.request(
            "GET", relative_url, headers={}
        )

        # Validate
        self.assertEqual(200, resp.status)
        self.assertEqual(object_data, body.decode())
