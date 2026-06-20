# Copyright 2026 Red Hat, Inc.
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

import os

from tempest.api.object_storage import base
from tempest.common import object_storage
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ObjectSymlinkTest(base.BaseObjectTest):
    """Tempest API tests for Swift symbolic link objects (symlinks)"""

    @classmethod
    def resource_setup(cls):
        super(ObjectSymlinkTest, cls).resource_setup()
        cls.containers = []

        # Check if symlink is supported via Swift capabilities API
        if not CONF.object_storage_feature_enabled.discoverability:
            raise cls.skipException(
                "Cannot detect symlink support: discoverability disabled")

        try:
            body = cls.capabilities_client.list_capabilities()
        except Exception as e:
            raise cls.skipException(
                f"Cannot retrieve Swift capabilities: {e}")

        # Symlink middleware registers as 'symlink' in capabilities
        if 'symlink' not in body:
            raise cls.skipException(
                "Symlink middleware not enabled in Swift configuration")

    @classmethod
    def resource_cleanup(cls):
        object_storage.delete_containers(
            cls.containers, cls.container_client, cls.object_client)
        super(ObjectSymlinkTest, cls).resource_cleanup()

    def _create_container(self):
        container_name = data_utils.rand_name('symlink-container')
        self.container_client.create_container(container_name)
        type(self).containers.append(container_name)
        return container_name

    def _upload_object(self, container_name, object_name, data):
        self.object_client.create_object(
            container_name, object_name, data=data)

    @decorators.idempotent_id('06b11169-e8a3-4660-97fd-d350f855042d')
    def test_symlink(self):
        """Test creating and accessing a basic symlink object"""
        container_name = self._create_container()
        object_name = "file.txt"
        file_content = os.urandom(20)
        self._upload_object(container_name, object_name, file_content)

        link_name = "link.txt"
        target = f"{container_name}/{object_name}"
        headers = {
            "X-Symlink-Target": target,
            "Content-Type": "application/symlink"
        }

        # Use PUT directly to ensure Content-Type is not stripped
        url = f"{container_name}/{link_name}"
        resp, _ = self.object_client.put(url, b'', headers=headers)
        self.assertEqual(201, resp.status)

        # Verify metadata
        resp, body = self.container_client.list_container_objects(
            container_name, params={'limit': 9999, 'format': 'json'})
        self.assertEqual(200, resp.status)

        symlink_target = None
        for obj in body:
            if obj['name'] == link_name:
                self.assertEqual('application/symlink', obj['content_type'])
                symlink_target = obj.get('symlink_path')
                break

        self.assertIsNotNone(symlink_target)
        expected_path = f"{container_name}/{object_name}"
        self.assertTrue(symlink_target.endswith(expected_path))

        # Download symlink
        resp, body = self.object_client.get_object(container_name, link_name)
        self.assertEqual(file_content, body)

    @decorators.idempotent_id('e13c6786-bbe8-4f8b-9b79-1216fe5879d1')
    def test_cross_container_symlink(self):
        """Test symlink pointing to object in another container"""
        source_container = self._create_container()
        object_name = "file.txt"
        file_content = os.urandom(20)
        self._upload_object(source_container, object_name, file_content)

        dest_container = self._create_container()
        link_name = "link.txt"
        target = f"{source_container}/{object_name}"
        headers = {
            "X-Symlink-Target": target,
            "Content-Type": "application/symlink"
        }

        url = f"{dest_container}/{link_name}"
        resp, _ = self.object_client.put(url, b'', headers=headers)
        self.assertEqual(201, resp.status)

        resp, body = self.object_client.get_object(dest_container, link_name)
        self.assertEqual(file_content, body)

    @decorators.idempotent_id('bc58348b-bb32-4e76-9346-815f0f55cfa0')
    def test_broken_symlink(self):
        """Test behavior of a symlink pointing to a non-existent target"""
        container_name = self._create_container()
        link_name = "broken_link.txt"
        target = f"{container_name}/missing.txt"
        headers = {
            "X-Symlink-Target": target,
            "Content-Type": "application/symlink"
        }

        # Swift may reject broken symlinks; skip if not allowed
        try:
            url = f"{container_name}/{link_name}"
            resp, _ = self.object_client.put(url, b'', headers=headers)
        except (lib_exc.BadRequest, lib_exc.UnexpectedContentType):
            self.skipTest(
                "Broken symlinks not allowed in this Swift deployment")

        self.assertEqual(201, resp.status)

        self.assertRaises(
            lib_exc.NotFound,
            self.object_client.get_object,
            container_name,
            link_name,
        )

    @decorators.idempotent_id('aa1f9d1e-4f00-4c92-b8d1-a36b2e62c9cd')
    def test_symlink_after_target_delete(self):
        """Test symlink behavior after its target object is deleted"""
        container_name = self._create_container()
        object_name = "file.txt"
        file_content = os.urandom(20)
        self._upload_object(container_name, object_name, file_content)

        link_name = "link.txt"
        target = f"{container_name}/{object_name}"
        headers = {
            "X-Symlink-Target": target,
            "Content-Type": "application/symlink"
        }

        url = f"{container_name}/{link_name}"
        resp, _ = self.object_client.put(url, b'', headers=headers)
        self.assertEqual(201, resp.status)

        resp, _ = self.object_client.delete_object(container_name, object_name)
        self.assertEqual(204, resp.status)

        self.assertRaises(
            lib_exc.NotFound,
            self.object_client.get_object,
            container_name,
            link_name,
        )
