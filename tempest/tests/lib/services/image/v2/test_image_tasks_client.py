# Copyright 2023 Red Hat, Inc.  All rights reserved.
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

from tempest.lib.services.image.v2 import tasks_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestImageTaskClient(base.BaseServiceTest):
    def setUp(self):
        super(TestImageTaskClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = tasks_client.TaskClient(
            fake_auth, 'image', 'regionOne')

    def test_list_task(self):
        fake_result = {

            "first": "/v2/tasks",
            "schema": "/v2/schemas/tasks",
            "tasks": [
                {
                    "id": "08b7e1c8-3821-4f54-b3b8-d6655d178cdf",
                    "owner": "fa6c8c1600f4444281658a23ee6da8e8",
                    "schema": "/v2/schemas/task",
                    "self": "/v2/tasks/08b7e1c8-3821-4f54-b3b8-d6655d178cdf",
                    "status": "processing",
                    "type": "import"
                    },
                {
                    "id": "231c311d-3557-4e23-afc4-6d98af1419e7",
                    "owner": "fa6c8c1600f4444281658a23ee6da8e8",
                    "schema": "/v2/schemas/task",
                    "self": "/v2/tasks/231c311d-3557-4e23-afc4-6d98af1419e7",
                    "status": "processing",
                    "type": "import"
                    }
                ]
            }
        self.check_service_client_function(
            self.client.list_tasks,
            'tempest.lib.common.rest_client.RestClient.get',
            fake_result,
            mock_args=['tasks'])

    def test_create_task(self):
        fake_result = {
            "type": "import",
            "input": {
                "import_from":
                "http://download.cirros-cloud.net/0.6.1/ \
                    cirros-0.6.1-x86_64-disk.img",
                "import_from_format": "qcow2",
                "image_properties": {
                    "disk_format": "qcow2",
                    "container_format": "bare"
                }
            }
            }
        self.check_service_client_function(
            self.client.create_task,
            'tempest.lib.common.rest_client.RestClient.post',
            fake_result,
            status=201)

    def test_show_task(self):
        fake_result = {
            "task_id": "08b7e1c8-3821-4f54-b3b8-d6655d178cdf"
            }
        self.check_service_client_function(
            self.client.show_tasks,
            'tempest.lib.common.rest_client.RestClient.get',
            fake_result,
            status=200,
            task_id="e485aab9-0907-4973-921c-bb6da8a8fcf8")
