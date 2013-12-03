# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Joe H. Rahme <joe.hakim.rahme@enovance.com>
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

from tempest.api.object_storage import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.test import attr
from tempest.test import HTTP_SUCCESS


class ObjectTempUrlTest(base.BaseObjectTest):

    tempurl_available = \
        config.TempestConfig().object_storage_feature_enabled.tempurl

    @classmethod
    def setUpClass(cls):
        super(ObjectTempUrlTest, cls).setUpClass()

        # skip this test if CORS isn't enabled in the conf file.
        if not cls.tempurl_available:
            skip_msg = ("%s skipped as TempUrl middleware not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

        cls.container_name = data_utils.rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)
        cls.containers = [cls.container_name]

        # update account metadata
        cls.key = 'Meta'
        cls.metadata = {'Temp-URL-Key': cls.key}
        cls.account_client.create_account_metadata(metadata=cls.metadata)
        cls.account_client_metadata, _ = \
            cls.account_client.list_account_metadata()

    @classmethod
    def tearDownClass(cls):
        resp, _ = cls.account_client.delete_account_metadata(
            metadata=cls.metadata)

        cls.delete_containers(cls.containers)

        # delete the user setup created
        cls.data.teardown_all()
        super(ObjectTempUrlTest, cls).tearDownClass()

    def setUp(self):
        super(ObjectTempUrlTest, self).setUp()
        # make sure the metadata has been set
        self.assertIn('x-account-meta-temp-url-key',
                      self.account_client_metadata)

        self.assertEqual(
            self.account_client_metadata['x-account-meta-temp-url-key'],
            self.key)

        # create object
        self.object_name = data_utils.rand_name(name='ObjectTemp')
        self.data = data_utils.arbitrary_string(size=len(self.object_name),
                                                base_text=self.object_name)
        self.object_client.create_object(self.container_name,
                                         self.object_name, self.data)

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

    @attr(type='gate')
    def test_get_object_using_temp_url(self):
        expires = self._get_expiry_date()

        # get a temp URL for the created object
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "GET",
                                 expires, self.key)

        # trying to get object using temp url within expiry time
        resp, body = self.object_client.get_object_using_temp_url(url)

        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.assertEqual(body, self.data)

        # Testing a HEAD on this Temp URL
        resp, body = self.object_client.head(url)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)

    @attr(type='gate')
    def test_get_object_using_temp_url_key_2(self):
        key2 = 'Meta2-'
        metadata = {'Temp-URL-Key-2': key2}
        self.account_client.create_account_metadata(metadata=metadata)

        self.account_client_metadata, _ = \
            self.account_client.list_account_metadata()
        self.assertIn('x-account-meta-temp-url-key-2',
                      self.account_client_metadata)

        expires = self._get_expiry_date()
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "GET",
                                 expires, key2)
        resp, body = self.object_client.get_object_using_temp_url(url)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
        self.assertEqual(body, self.data)

    @attr(type='gate')
    def test_put_object_using_temp_url(self):
        # make sure the metadata has been set
        new_data = data_utils.arbitrary_string(
            size=len(self.object_name),
            base_text=data_utils.rand_name(name="random"))

        expires = self._get_expiry_date()
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "PUT",
                                 expires, self.key)

        # trying to put random data in the object using temp url
        resp, body = self.object_client.put_object_using_temp_url(
            url, new_data)

        self.assertIn(int(resp['status']), HTTP_SUCCESS)

        # Testing a HEAD on this Temp URL
        resp, body = self.object_client.head(url)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)

        # Validate that the content of the object has been modified
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "GET",
                                 expires, self.key)

        _, body = self.object_client.get_object_using_temp_url(url)
        self.assertEqual(body, new_data)

    @attr(type=['gate', 'negative'])
    def test_get_object_after_expiration_time(self):

        expires = self._get_expiry_date(1)
        # get a temp URL for the created object
        url = self._get_temp_url(self.container_name,
                                 self.object_name, "GET",
                                 expires, self.key)

        # temp URL is valid for 1 seconds, let's wait 2
        time.sleep(2)

        self.assertRaises(exceptions.Unauthorized,
                          self.object_client.get_object_using_temp_url,
                          url)
