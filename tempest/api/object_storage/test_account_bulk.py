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
from tempest.common import object_storage
from tempest.common import utils
from tempest.lib import decorators


class BulkTest(base.BaseObjectTest):
    """Test bulk operation of archived file"""

    def setUp(self):
        super(BulkTest, self).setUp()
        self.containers = []

    def tearDown(self):
        # NOTE(andreaf) BulkTests needs to cleanup containers after each
        # test is executed.
        object_storage.delete_containers(self.containers,
                                         self.container_client,
                                         self.object_client)
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

    def _upload_archive(self, filepath):
        # upload an archived file
        with open(filepath) as fh:
            mydata = fh.read()
            resp = self.bulk_client.upload_archive(
                upload_path='', data=mydata, archive_file_format='tar')
        return resp

    def _check_contents_deleted(self, container_name):
        param = {'format': 'txt'}
        resp, body = self.account_client.list_account_containers(param)
        self.assertHeaders(resp, 'Account', 'GET')
        self.assertNotIn(container_name, body)

    @decorators.idempotent_id('a407de51-1983-47cc-9f14-47c2b059413c')
    @utils.requires_ext(extension='bulk_upload', service='object')
    def test_extract_archive(self):
        """Test bulk operation of file upload with an archived file"""
        filepath, container_name, object_name = self._create_archive()
        resp = self._upload_archive(filepath)
        self.containers.append(container_name)

        self.assertHeaders(resp.response, 'Account', 'PUT')

        param = {'format': 'json'}
        resp, body = self.account_client.list_account_containers(param)

        self.assertHeaders(resp, 'Account', 'GET')

        self.assertIn(container_name, [b['name'] for b in body])

        param = {'format': 'json'}
        resp, contents_list = self.container_client.list_container_objects(
            container_name, param)

        self.assertHeaders(resp, 'Container', 'GET')

        self.assertIn(object_name, [c['name'] for c in contents_list])

    @decorators.idempotent_id('c075e682-0d2a-43b2-808d-4116200d736d')
    @utils.requires_ext(extension='bulk_delete', service='object')
    def test_bulk_delete(self):
        """Test bulk operation of deleting multiple files"""
        filepath, container_name, object_name = self._create_archive()
        self._upload_archive(filepath)

        data = '%s/%s\n%s' % (container_name, object_name, container_name)
        resp = self.bulk_client.delete_bulk_data(data=data)

        self.assertHeaders(resp.response, 'Account', 'DELETE')

        # Check if uploaded contents are completely deleted
        self._check_contents_deleted(container_name)

    @decorators.idempotent_id('dbea2bcb-efbb-4674-ac8a-a5a0e33d1d79')
    @utils.requires_ext(extension='bulk_delete', service='object')
    def test_bulk_delete_by_POST(self):
        """Test bulk operation of deleting multiple files by HTTP POST"""
        filepath, container_name, object_name = self._create_archive()
        self._upload_archive(filepath)

        data = '%s/%s\n%s' % (container_name, object_name, container_name)

        resp = self.bulk_client.delete_bulk_data_with_post(data=data)

        self.assertHeaders(resp.response, 'Account', 'POST')

        # Check if uploaded contents are completely deleted
        self._check_contents_deleted(container_name)
