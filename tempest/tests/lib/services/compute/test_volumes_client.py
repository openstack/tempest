# Copyright 2015 NEC Corporation.  All rights reserved.
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

import copy

from oslotest import mockpatch

from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import volumes_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestVolumesClient(base.BaseComputeServiceTest):

    FAKE_VOLUME = {
        "id": "521752a6-acf6-4b2d-bc7a-119f9148cd8c",
        "displayName": u"v\u12345ol-001",
        "displayDescription": u"Another \u1234volume.",
        "size": 30,
        "status": "Active",
        "volumeType": "289da7f8-6440-407c-9fb4-7db01ec49164",
        "metadata": {
            "contents": "junk"
        },
        "availabilityZone": "us-east1",
        "snapshotId": None,
        "attachments": [],
        "createdAt": "2012-02-14T20:53:07Z"
    }

    FAKE_VOLUMES = {"volumes": [FAKE_VOLUME]}

    def setUp(self):
        super(TestVolumesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = volumes_client.VolumesClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_volumes(self, bytes_body=False, **params):
        self.check_service_client_function(
            self.client.list_volumes,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_VOLUMES, to_utf=bytes_body, **params)

    def test_list_volumes_with_str_body(self):
        self._test_list_volumes()

    def test_list_volumes_with_byte_body(self):
        self._test_list_volumes(bytes_body=True)

    def test_list_volumes_with_params(self):
        self._test_list_volumes(name='fake')

    def _test_show_volume(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_volume,
            'tempest.lib.common.rest_client.RestClient.get',
            {"volume": self.FAKE_VOLUME},
            to_utf=bytes_body, volume_id=self.FAKE_VOLUME['id'])

    def test_show_volume_with_str_body(self):
        self._test_show_volume()

    def test_show_volume_with_bytes_body(self):
        self._test_show_volume(bytes_body=True)

    def _test_create_volume(self, bytes_body=False):
        post_body = copy.deepcopy(self.FAKE_VOLUME)
        del post_body['id']
        del post_body['createdAt']
        del post_body['status']
        self.check_service_client_function(
            self.client.create_volume,
            'tempest.lib.common.rest_client.RestClient.post',
            {"volume": self.FAKE_VOLUME},
            to_utf=bytes_body, status=200, **post_body)

    def test_create_volume_with_str_body(self):
        self._test_create_volume()

    def test_create_volume_with_bytes_body(self):
        self._test_create_volume(bytes_body=True)

    def test_delete_volume(self):
        self.check_service_client_function(
            self.client.delete_volume,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202, volume_id=self.FAKE_VOLUME['id'])

    def test_is_resource_deleted_true(self):
        module = ('tempest.lib.services.compute.volumes_client.'
                  'VolumesClient.show_volume')
        self.useFixture(mockpatch.Patch(
            module, side_effect=lib_exc.NotFound))
        self.assertTrue(self.client.is_resource_deleted('fake-id'))

    def test_is_resource_deleted_false(self):
        module = ('tempest.lib.services.compute.volumes_client.'
                  'VolumesClient.show_volume')
        self.useFixture(mockpatch.Patch(
            module, return_value={}))
        self.assertFalse(self.client.is_resource_deleted('fake-id'))
