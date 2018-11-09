# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

from oslo_serialization import jsonutils as json

from tempest.lib.services.volume.v3 import volumes_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestVolumesClient(base.BaseServiceTest):

    FAKE_VOLUME_SUMMARY = {
        "volume-summary": {
            "total_size": 4,
            "total_count": 4,
        }
    }

    FAKE_VOLUME_METADATA_ITEM = {
        "meta": {
            "name": "metadata1"
        }
    }

    FAKE_VOLUME_IMAGE_METADATA = {
        "metadata": {
            "key1": "value1",
            "key2": "value2"
        }
    }

    def setUp(self):
        super(TestVolumesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = volumes_client.VolumesClient(fake_auth,
                                                   'volume',
                                                   'regionOne')

    def _test_retype_volume(self, bytes_body=False):
        kwargs = {
            "new_type": "dedup-tier-replication",
            "migration_policy": "never"
        }

        self.check_service_client_function(
            self.client.retype_volume,
            'tempest.lib.common.rest_client.RestClient.post',
            {},
            to_utf=bytes_body,
            status=202,
            volume_id="a3be971b-8de5-4bdf-bdb8-3d8eb0fb69f8",
            **kwargs
        )

    def _test_force_detach_volume(self, bytes_body=False):
        kwargs = {
            'attachment_id': '6980e295-920f-412e-b189-05c50d605acd',
            'connector': {
                'initiator': 'iqn.2017-04.org.fake:01'
            }
        }

        self.check_service_client_function(
            self.client.force_detach_volume,
            'tempest.lib.common.rest_client.RestClient.post',
            {},
            to_utf=bytes_body,
            status=202,
            volume_id="a3be971b-8de5-4bdf-bdb8-3d8eb0fb69f8",
            **kwargs
        )

    def _test_show_volume_metadata_item(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_volume_metadata_item,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_VOLUME_METADATA_ITEM,
            to_utf=bytes_body,
            volume_id="a3be971b-8de5-4bdf-bdb8-3d8eb0fb69f8",
            id="key1")

    def _test_show_volume_image_metadata(self, bytes_body=False):
        fake_volume_id = "a3be971b-8de5-4bdf-bdb8-3d8eb0fb69f8"
        self.check_service_client_function(
            self.client.show_volume_image_metadata,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_VOLUME_IMAGE_METADATA,
            to_utf=bytes_body,
            mock_args=['volumes/%s/action' % fake_volume_id,
                       json.dumps({"os-show_image_metadata": {}})],
            volume_id=fake_volume_id)

    def _test_show_volume_summary(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_volume_summary,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_VOLUME_SUMMARY,
            bytes_body)

    def test_force_detach_volume_with_str_body(self):
        self._test_force_detach_volume()

    def test_force_detach_volume_with_bytes_body(self):
        self._test_force_detach_volume(bytes_body=True)

    def test_show_volume_metadata_item_with_str_body(self):
        self._test_show_volume_metadata_item()

    def test_show_volume_metadata_item_with_bytes_body(self):
        self._test_show_volume_metadata_item(bytes_body=True)

    def test_show_volume_image_metadata_with_str_body(self):
        self._test_show_volume_image_metadata()

    def test_show_volume_image_metadata_with_bytes_body(self):
        self._test_show_volume_image_metadata(bytes_body=True)

    def test_retype_volume_with_str_body(self):
        self._test_retype_volume()

    def test_retype_volume_with_bytes_body(self):
        self._test_retype_volume(bytes_body=True)

    def test_show_volume_summary_with_str_body(self):
        self._test_show_volume_summary()

    def test_show_volume_summary_with_bytes_body(self):
        self._test_show_volume_summary(bytes_body=True)
