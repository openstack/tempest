# Copyright 2016 EasyStack. All rights reserved.
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

from tempest.lib.services.image.v2 import namespace_objects_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestNamespaceObjectClient(base.BaseServiceTest):
    FAKE_CREATE_SHOW_OBJECTS = {
        "created_at": "2016-09-19T18:20:56Z",
        "description": "You can configure the CPU limits.",
        "name": "CPU Limits",
        "properties": {
            "quota:cpu_period": {
                "description": "Specifies the enforcement interval",
                "maximum": 1000000,
                "minimum": 1000,
                "title": "Quota: CPU Period",
                "type": "integer"
            },
            "quota:cpu_quota": {
                "description": "Specifies the maximum allowed bandwidth ",
                "title": "Quota: CPU Quota",
                "type": "integer"
            },
            "quota:cpu_shares": {
                "description": "Specifies the proportional weighted share.",
                "title": "Quota: CPU Shares",
                "type": "integer"
            }
        },
        "required": [],
        "schema": "/v2/schemas/metadefs/object",
        "self": "/v2/metadefs/namespaces/OS::Compute::Quota/objects/CPU",
        "updated_at": "2016-09-19T18:20:56Z"
    }

    FAKE_LIST_OBJECTS = {
        "objects": [
            {
                "created_at": "2016-09-18T18:16:35Z",
                "description": "You can configure the CPU limits.",
                "name": "CPU Limits",
                "properties": {
                    "quota:cpu_period": {
                        "description": "Specifies the enforcement interval ",
                        "maximum": 1000000,
                        "minimum": 1000,
                        "title": "Quota: CPU Period",
                        "type": "integer"
                    },
                    "quota:cpu_quota": {
                        "description": "Specifies the maximum.",
                        "title": "Quota: CPU Quota",
                        "type": "integer"
                    },
                    "quota:cpu_shares": {
                        "description": " Desc.",
                        "title": "Quota: CPU Shares",
                        "type": "integer"
                    }
                },
                "required": [],
                "schema": "/v2/schemas/metadefs/object",
                "self":
                    "/v2/metadefs/namespaces/OS::Compute::Quota/objects/CPU"
            },
            {
                "created_at": "2016-09-18T18:16:35Z",
                "description": "Using disk I/O quotas.",
                "name": "Disk QoS",
                "properties": {
                    "quota:disk_read_bytes_sec": {
                        "description": "Sets disk I/O quota.",
                        "title": "Quota: Disk read bytes / sec",
                        "type": "integer"
                    },
                    "quota:disk_read_iops_sec": {
                        "description": "Sets disk I/O quota",
                        "title": "Quota: Disk read IOPS / sec",
                        "type": "integer"
                    },
                    "quota:disk_total_bytes_sec": {
                        "description": "Sets disk I/O quota.",
                        "title": "Quota: Disk Total Bytes / sec",
                        "type": "integer"
                    },
                    "quota:disk_total_iops_sec": {
                        "description": "Sets disk I/O quota.",
                        "title": "Quota: Disk Total IOPS / sec",
                        "type": "integer"
                    },
                    "quota:disk_write_bytes_sec": {
                        "description": "Sets disk I/O quota.",
                        "title": "Quota: Disk Write Bytes / sec",
                        "type": "integer"
                    },
                    "quota:disk_write_iops_sec": {
                        "description": "Sets disk I/O quota.",
                        "title": "Quota: Disk Write IOPS / sec",
                        "type": "integer"
                    }
                },
                "required": [],
                "schema": "/v2/schemas/metadefs/object",
                "self":
                "/v2/metadefs/namespaces/OS::Compute::Quota/objects/Disk QoS"
            },
        ],
        "schema": "v2/schemas/metadefs/objects"
    }

    FAKE_UPDATE_OBJECTS = {
        "description": "You can configure the CPU limits.",
        "name": "CPU",
        "properties": {
            "quota:cpu_shares": {
                "description": "Specify.",
                "title": "Quota: CPU Shares",
                "type": "integer"
            }
        },
        "required": []
    }

    def setUp(self):
        super(TestNamespaceObjectClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = namespace_objects_client.NamespaceObjectsClient(
            fake_auth, 'image', 'regionOne')

    def _test_create_namespace_objects(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_namespace_object,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_SHOW_OBJECTS,
            bytes_body, status=201,
            namespace="OS::Compute::Hypervisor",
            object_name="OS::Glance::Image")

    def _test_list_namespace_objects(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_namespace_objects,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_OBJECTS,
            bytes_body,
            namespace="OS::Compute::Hypervisor")

    def _test_show_namespace_objects(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_namespace_object,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CREATE_SHOW_OBJECTS,
            bytes_body,
            namespace="OS::Compute::Hypervisor",
            object_name="OS::Glance::Image")

    def _test_update_namespace_objects(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_namespace_object,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_OBJECTS,
            bytes_body,
            namespace="OS::Compute::Hypervisor",
            object_name="OS::Glance::Image",
            name="CPU")

    def test_create_namespace_object_with_str_body(self):
        self._test_create_namespace_objects()

    def test_create_namespace_object_with_bytes_body(self):
        self._test_create_namespace_objects(bytes_body=True)

    def test_list_namespace_object_with_str_body(self):
        self._test_list_namespace_objects()

    def test_list_namespace_object_with_bytes_body(self):
        self._test_list_namespace_objects(bytes_body=True)

    def test_show_namespace_object_with_str_body(self):
        self._test_show_namespace_objects()

    def test_show_namespace_object_with_bytes_body(self):
        self._test_show_namespace_objects(bytes_body=True)

    def test_update_namespace_object_with_str_body(self):
        self._test_update_namespace_objects()

    def test_update_namespace_object_with_bytes_body(self):
        self._test_update_namespace_objects(bytes_body=True)

    def test_delete_namespace_objects(self):
        self.check_service_client_function(
            self.client.delete_namespace_object,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, namespace="OS::Compute::Hypervisor",
            object_name="OS::Glance::Image",
            status=204)
