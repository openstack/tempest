# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.image.v2 import image_members_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestImageMembersClient(base.BaseServiceTest):
    FAKE_CREATE_SHOW_UPDATE_IMAGE_MEMBER = {
        "status": "pending",
        "created_at": "2013-11-26T07:21:21Z",
        "updated_at": "2013-11-26T07:21:21Z",
        "image_id": "0ae74cc5-5147-4239-9ce2-b0c580f7067e",
        "member_id": "8989447062e04a818baf9e073fd04fa7",
        "schema": "/v2/schemas/member"
    }

    def setUp(self):
        super(TestImageMembersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = image_members_client.ImageMembersClient(fake_auth,
                                                              'image',
                                                              'regionOne')

    def _test_show_image_member(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_image_member,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CREATE_SHOW_UPDATE_IMAGE_MEMBER,
            bytes_body,
            image_id="0ae74cc5-5147-4239-9ce2-b0c580f7067e",
            member_id="8989447062e04a818baf9e073fd04fa7")

    def _test_create_image_member(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_image_member,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_SHOW_UPDATE_IMAGE_MEMBER,
            bytes_body,
            image_id="0ae74cc5-5147-4239-9ce2-b0c580f7067e",
            member_id="8989447062e04a818baf9e073fd04fa7")

    def _test_update_image_member(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_image_member,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_CREATE_SHOW_UPDATE_IMAGE_MEMBER,
            bytes_body,
            image_id="0ae74cc5-5147-4239-9ce2-b0c580f7067e",
            member_id="8989447062e04a818baf9e073fd04fa7",
            schema="/v2/schemas/member2")

    def test_show_image_member_with_str_body(self):
        self._test_show_image_member()

    def test_show_image_member_with_bytes_body(self):
        self._test_show_image_member(bytes_body=True)

    def test_create_image_member_with_str_body(self):
        self._test_create_image_member()

    def test_create_image_member_with_bytes_body(self):
        self._test_create_image_member(bytes_body=True)

    def test_delete_image_member(self):
        self.check_service_client_function(
            self.client.delete_image_member,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            image_id="0ae74cc5-5147-4239-9ce2-b0c580f7067e",
            member_id="8989447062e04a818baf9e073fd04fa7",
            status=204)

    def test_update_image_member_with_str_body(self):
        self._test_update_image_member()

    def test_update_image_member_with_bytes_body(self):
        self._test_update_image_member(bytes_body=True)
