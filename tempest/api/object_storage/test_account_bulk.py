# Copyright 2013 NTT Corporation
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

import tarfile
import tempfile

from tempest.api.object_storage import base
from tempest.common import custom_matchers
from tempest import test


class BulkTest(base.BaseObjectTest):

    def setUp(self):
        super(BulkTest, self).setUp()
        self.containers = []

    def tearDown(self):
        self.delete_containers(self.containers)
        super(BulkTest, self).tearDown()

    def _create_archive(self):
        # Create an archived file for bulk upload testing.
        # Directory and files contained in the directory correspond to
        # container and subsidiary objects.
        tmp_dir = tempfile.mkdtemp()
        tmp_file = tempfile.mkstemp(dir=tmp_dir)

        # Extract a container name and an object name
        container_name = tmp_dir.split("/")[-1]
        object_name = tmp_file[1].split("/")[-1]

        # Create tar file
        tarpath = tempfile.NamedTemporaryFile(suffix=".tar")
        tar = tarfile.open(None, 'w', tarpath)
        tar.add(tmp_dir, arcname=container_name)
        tar.close()
        tarpath.flush()

        return tarpath.name, container_name, object_name

    @test.attr(type='gate')
    def test_extract_archive(self):
        # Test bulk operation of file upload with an archived file
        filepath, container_name, object_name = self._create_archive()

        params = {'extract-archive': 'tar'}
        with open(filepath) as fh:
            mydata = fh.read()
            resp, body = self.account_client.create_account(data=mydata,
                                                            params=params)

        self.containers.append(container_name)

        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)

        # When uploading an archived file with the bulk operation, the response
        # does not contain 'content-length' header. This is the special case,
        # therefore the existence of response headers is checked without
        # custom matcher.
        self.assertIn('transfer-encoding', resp)
        self.assertIn('content-type', resp)
        self.assertIn('x-trans-id', resp)
        self.assertIn('date', resp)

        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

        param = {'format': 'json'}
        resp, body = self.account_client.list_account_containers(param)

        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertIn(container_name, [b['name'] for b in body])

        param = {'format': 'json'}
        resp, contents_list = self.container_client.list_container_contents(
            container_name, param)

        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Container', 'GET')

        self.assertIn(object_name, [c['name'] for c in contents_list])

    @test.attr(type='gate')
    def test_bulk_delete(self):
        # Test bulk operation of deleting multiple files
        filepath, container_name, object_name = self._create_archive()

        params = {'extract-archive': 'tar'}
        with open(filepath) as fh:
            mydata = fh.read()
            resp, body = self.account_client.create_account(data=mydata,
                                                            params=params)

        data = '%s/%s\n%s' % (container_name, object_name, container_name)
        params = {'bulk-delete': ''}
        resp, body = self.account_client.delete_account(data=data,
                                                        params=params)

        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)

        # When deleting multiple files using the bulk operation, the response
        # does not contain 'content-length' header. This is the special case,
        # therefore the existence of response headers is checked without
        # custom matcher.
        self.assertIn('transfer-encoding', resp)
        self.assertIn('content-type', resp)
        self.assertIn('x-trans-id', resp)
        self.assertIn('date', resp)

        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())

        # Check if a container is deleted
        param = {'format': 'txt'}
        resp, body = self.account_client.list_account_containers(param)

        self.assertIn(int(resp['status']), test.HTTP_SUCCESS)
        self.assertHeaders(resp, 'Account', 'GET')

        self.assertNotIn(container_name, body)
