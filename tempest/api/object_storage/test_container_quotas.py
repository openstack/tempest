# Copyright 2013 Cloudwatt
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.object_storage import base
from tempest import config
from tempest import test

CONF = config.CONF
QUOTA_BYTES = 10
QUOTA_COUNT = 3


class ContainerQuotasTest(base.BaseObjectTest):
    """Attemps to test the perfect behavior of quotas in a container."""

    def setUp(self):
        """Creates and sets a container with quotas.

        Quotas are set by adding meta values to the container,
        and are validated when set:
          - X-Container-Meta-Quota-Bytes:
                     Maximum size of the container, in bytes.
          - X-Container-Meta-Quota-Count:
                     Maximum object count of the container.
        """
        super(ContainerQuotasTest, self).setUp()
        self.container_name = data_utils.rand_name(name="TestContainer")
        self.container_client.create_container(self.container_name)
        metadata = {"quota-bytes": str(QUOTA_BYTES),
                    "quota-count": str(QUOTA_COUNT), }
        self.container_client.update_container_metadata(
            self.container_name, metadata)

    def tearDown(self):
        """Cleans the container of any object after each test."""
        self.delete_containers([self.container_name])
        super(ContainerQuotasTest, self).tearDown()

    @test.idempotent_id('9a0fb034-86af-4df0-86fa-f8bd7db21ae0')
    @test.requires_ext(extension='container_quotas', service='object')
    @test.attr(type="smoke")
    def test_upload_valid_object(self):
        """Attempts to uploads an object smaller than the bytes quota."""
        object_name = data_utils.rand_name(name="TestObject")
        data = data_utils.arbitrary_string(QUOTA_BYTES)

        nbefore = self._get_bytes_used()

        resp, _ = self.object_client.create_object(
            self.container_name, object_name, data)
        self.assertHeaders(resp, 'Object', 'PUT')

        nafter = self._get_bytes_used()
        self.assertEqual(nbefore + len(data), nafter)

    @test.idempotent_id('22eeeb2b-3668-4160-baef-44790f65a5a0')
    @test.requires_ext(extension='container_quotas', service='object')
    @test.attr(type="smoke")
    def test_upload_large_object(self):
        """Attempts to upload an object lagger than the bytes quota."""
        object_name = data_utils.rand_name(name="TestObject")
        data = data_utils.arbitrary_string(QUOTA_BYTES + 1)

        nbefore = self._get_bytes_used()

        self.assertRaises(lib_exc.OverLimit,
                          self.object_client.create_object,
                          self.container_name, object_name, data)

        nafter = self._get_bytes_used()
        self.assertEqual(nbefore, nafter)

    @test.idempotent_id('3a387039-697a-44fc-a9c0-935de31f426b')
    @test.requires_ext(extension='container_quotas', service='object')
    @test.attr(type="smoke")
    def test_upload_too_many_objects(self):
        """Attempts to upload many objects that exceeds the count limit."""
        for _ in range(QUOTA_COUNT):
            name = data_utils.rand_name(name="TestObject")
            self.object_client.create_object(self.container_name, name, "")

        nbefore = self._get_object_count()
        self.assertEqual(nbefore, QUOTA_COUNT)

        self.assertRaises(lib_exc.OverLimit,
                          self.object_client.create_object,
                          self.container_name, "OverQuotaObject", "")

        nafter = self._get_object_count()
        self.assertEqual(nbefore, nafter)

    def _get_container_metadata(self):
        resp, _ = self.container_client.list_container_metadata(
            self.container_name)
        return resp

    def _get_object_count(self):
        resp = self._get_container_metadata()
        return int(resp["x-container-object-count"])

    def _get_bytes_used(self):
        resp = self._get_container_metadata()
        return int(resp["x-container-bytes-used"])
