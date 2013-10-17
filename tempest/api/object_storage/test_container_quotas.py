# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import testtools

from tempest.api.object_storage import base
from tempest.common.utils.data_utils import arbitrary_string
from tempest.common.utils.data_utils import rand_name
from tempest import config
from tempest import exceptions
from tempest.test import attr
from tempest.test import HTTP_SUCCESS

QUOTA_BYTES = 10
QUOTA_COUNT = 3
SKIP_MSG = "Container quotas middleware not available."


class ContainerQuotasTest(base.BaseObjectTest):
    """Attemps to test the perfect behavior of quotas in a container."""
    container_quotas_available = \
        config.TempestConfig().object_storage_feature_enabled.container_quotas

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
        self.container_name = rand_name(name="TestContainer")
        self.container_client.create_container(self.container_name)
        metadata = {"quota-bytes": str(QUOTA_BYTES),
                    "quota-count": str(QUOTA_COUNT), }
        self.container_client.update_container_metadata(
            self.container_name, metadata)

    def tearDown(self):
        """Cleans the container of any object after each test."""
        self.delete_containers([self.container_name])
        super(ContainerQuotasTest, self).tearDown()

    @testtools.skipIf(not container_quotas_available, SKIP_MSG)
    @attr(type="smoke")
    def test_upload_valid_object(self):
        """Attempts to uploads an object smaller than the bytes quota."""
        object_name = rand_name(name="TestObject")
        data = arbitrary_string(QUOTA_BYTES)

        nbefore = self._get_bytes_used()

        resp, _ = self.object_client.create_object(
            self.container_name, object_name, data)
        self.assertIn(int(resp['status']), HTTP_SUCCESS)

        nafter = self._get_bytes_used()
        self.assertEqual(nbefore + len(data), nafter)

    @testtools.skipIf(not container_quotas_available, SKIP_MSG)
    @attr(type="smoke")
    def test_upload_large_object(self):
        """Attempts to upload an object lagger than the bytes quota."""
        object_name = rand_name(name="TestObject")
        data = arbitrary_string(QUOTA_BYTES + 1)

        nbefore = self._get_bytes_used()

        self.assertRaises(exceptions.OverLimit,
                          self.object_client.create_object,
                          self.container_name, object_name, data)

        nafter = self._get_bytes_used()
        self.assertEqual(nbefore, nafter)

    @testtools.skipIf(not container_quotas_available, SKIP_MSG)
    @attr(type="smoke")
    def test_upload_too_many_objects(self):
        """Attempts to upload many objects that exceeds the count limit."""
        for _ in range(QUOTA_COUNT):
            name = rand_name(name="TestObject")
            self.object_client.create_object(self.container_name, name, "")

        nbefore = self._get_object_count()
        self.assertEqual(nbefore, QUOTA_COUNT)

        self.assertRaises(exceptions.OverLimit,
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
