# Copyright 2017 AT&T Corporation.
# All rights reserved.
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

from tempest.lib.services.network import metering_labels_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestMeteringLabelsClient(base.BaseServiceTest):

    FAKE_METERING_LABELS = {
        "metering_labels": [
            {
                "project_id": "45345b0ee1ea477fac0f541b2cb79cd4",
                "tenant_id": "45345b0ee1ea477fac0f541b2cb79cd4",
                "description": "label1 description",
                "name": "label1",
                "id": "a6700594-5b7a-4105-8bfe-723b346ce866",
                "shared": False
            },
            {
                "project_id": "45345b0ee1ea477fac0f541b2cb79cd4",
                "tenant_id": "45345b0ee1ea477fac0f541b2cb79cd4",
                "description": "label2 description",
                "name": "label2",
                "id": "e131d186-b02d-4c0b-83d5-0c0725c4f812",
                "shared": False
            }
        ]
    }

    FAKE_METERING_LABEL_ID = "a6700594-5b7a-4105-8bfe-723b346ce866"

    def setUp(self):
        super(TestMeteringLabelsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.metering_labels_client = \
            metering_labels_client.MeteringLabelsClient(
                fake_auth, "network", "regionOne")

    def _test_list_metering_labels(self, bytes_body=False):
        self.check_service_client_function(
            self.metering_labels_client.list_metering_labels,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_METERING_LABELS,
            bytes_body,
            200)

    def _test_create_metering_label(self, bytes_body=False):
        self.check_service_client_function(
            self.metering_labels_client.create_metering_label,
            "tempest.lib.common.rest_client.RestClient.post",
            {"metering_label": self.FAKE_METERING_LABELS[
                "metering_labels"][1]},
            bytes_body,
            201,
            name="label1",
            description="label1 description",
            shared=False)

    def _test_show_metering_label(self, bytes_body=False):
        self.check_service_client_function(
            self.metering_labels_client.show_metering_label,
            "tempest.lib.common.rest_client.RestClient.get",
            {"metering_label": self.FAKE_METERING_LABELS[
                "metering_labels"][0]},
            bytes_body,
            200,
            metering_label_id=self.FAKE_METERING_LABEL_ID)

    def test_delete_metering_label(self):
        self.check_service_client_function(
            self.metering_labels_client.delete_metering_label,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            metering_label_id=self.FAKE_METERING_LABEL_ID)

    def test_list_metering_labels_with_str_body(self):
        self._test_list_metering_labels()

    def test_list_metering_labels_with_bytes_body(self):
        self._test_list_metering_labels(bytes_body=True)

    def test_create_metering_label_with_str_body(self):
        self._test_create_metering_label()

    def test_create_metering_label_with_bytes_body(self):
        self._test_create_metering_label(bytes_body=True)

    def test_show_metering_label_with_str_body(self):
        self._test_show_metering_label()

    def test_show_metering_label_with_bytes_body(self):
        self._test_show_metering_label(bytes_body=True)
