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

from six.moves.urllib import parse as urlparse
from tempest_lib.common.utils import data_utils

from tempest.api.object_storage import base
from tempest import test
from tempest_lib import decorators


class ObjectFormPostTest(base.BaseObjectTest):

    metadata = {}
    containers = []

    @classmethod
    def resource_setup(cls):
        super(ObjectFormPostTest, cls).resource_setup()
        cls.container_name = data_utils.rand_name(name='TestContainer')
        cls.object_name = data_utils.rand_name(name='ObjectTemp')

        cls.container_client.create_container(cls.container_name)
        cls.containers = [cls.container_name]

        cls.key = 'Meta'
        cls.metadata = {'Temp-URL-Key': cls.key}
        cls.account_client.create_account_metadata(metadata=cls.metadata)

    def setUp(self):
        super(ObjectFormPostTest, self).setUp()

        # make sure the metadata has been set
        account_client_metadata, _ = \
            self.account_client.list_account_metadata()
        #Bug = 1417477
        #self.assertIn('x-account-meta-temp-url-key',
        #              account_client_metadata)
        #self.assertEqual(
        #    account_client_metadata['x-account-meta-temp-url-key'],
        #    self.key)

    @classmethod
    def resource_cleanup(cls):
        #Bug = 1417477
        #cls.account_client.delete_account_metadata(metadata=cls.metadata)
        cls.delete_containers(cls.containers)
        super(ObjectFormPostTest, cls).resource_cleanup()

    def get_multipart_form(self, expires=600):
        path = "%s/%s/%s" % (
            urlparse.urlparse(self.container_client.base_url).path,
            self.container_name,
            self.object_name)

        redirect = ''
        max_file_size = 104857600
        max_file_count = 10
        expires += int(time.time())
        hmac_body = '%s\n%s\n%s\n%s\n%s' % (path,
                                            redirect,
                                            max_file_size,
                                            max_file_count,
                                            expires)

        signature = hmac.new(self.key, hmac_body, hashlib.sha1).hexdigest()

        fields = {'redirect': redirect,
                  'max_file_size': str(max_file_size),
                  'max_file_count': str(max_file_count),
                  'expires': str(expires),
                  'signature': signature}

        boundary = '--boundary--'
        data = []
        for (key, value) in fields.items():
            data.append('--' + boundary)
            data.append('Content-Disposition: form-data; name="%s"' % key)
            data.append('')
            data.append(value)

        data.append('--' + boundary)
        data.append('Content-Disposition: form-data; '
                    'name="file1"; filename="testfile"')
        data.append('Content-Type: application/octet-stream')
        data.append('')
        data.append('hello world')

        data.append('--' + boundary + '--')
        data.append('')

        body = '\r\n'.join(data)
        content_type = 'multipart/form-data; boundary=%s' % boundary
        return body, content_type

    @decorators.skip_because(bug="1417485")
    @test.idempotent_id('80fac02b-6e54-4f7b-be0d-a965b5cbef76')
    @test.requires_ext(extension='formpost', service='object')
    def test_post_object_using_form(self):
        body, content_type = self.get_multipart_form()

        headers = {'Content-Type': content_type,
                   'Content-Length': str(len(body))}

        url = "%s/%s" % (self.container_name, self.object_name)

        resp, body = self.object_client.post(url, body, headers=headers)
        self.assertHeaders(resp, "Object", "POST")

        # Ensure object is available
        resp, body = self.object_client.get("%s/%s%s" % (
            self.container_name, self.object_name, "testfile"))
        self.assertHeaders(resp, "Object", "GET")
        self.assertEqual(body, "hello world")
