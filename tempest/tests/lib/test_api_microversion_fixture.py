# Copyright 2019 NEC Corporation.
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

from tempest.lib.common import api_microversion_fixture
from tempest.lib.services.compute import base_compute_client
from tempest.lib.services.placement import base_placement_client
from tempest.lib.services.volume import base_client
from tempest.tests import base


class TestAPIMicroversionFixture(base.TestCase):
    def setUp(self):
        super(TestAPIMicroversionFixture, self).setUp()
        # Verify that all the microversion are reset back to None
        # by Fixture.
        self.assertIsNone(base_compute_client.COMPUTE_MICROVERSION)
        self.assertIsNone(base_client.VOLUME_MICROVERSION)
        self.assertIsNone(base_placement_client.PLACEMENT_MICROVERSION)

    def test_compute_microversion(self):
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            compute_microversion='2.10'))
        self.assertEqual('2.10', base_compute_client.COMPUTE_MICROVERSION)
        self.assertIsNone(base_client.VOLUME_MICROVERSION)
        self.assertIsNone(base_placement_client.PLACEMENT_MICROVERSION)

    def test_volume_microversion(self):
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            volume_microversion='3.10'))
        self.assertIsNone(base_compute_client.COMPUTE_MICROVERSION)
        self.assertEqual('3.10', base_client.VOLUME_MICROVERSION)
        self.assertIsNone(base_placement_client.PLACEMENT_MICROVERSION)

    def test_placement_microversion(self):
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            placement_microversion='1.10'))
        self.assertIsNone(base_compute_client.COMPUTE_MICROVERSION)
        self.assertIsNone(base_client.VOLUME_MICROVERSION)
        self.assertEqual('1.10', base_placement_client.PLACEMENT_MICROVERSION)

    def test_multiple_service_microversion(self):
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            compute_microversion='2.10', volume_microversion='3.10',
            placement_microversion='1.10'))
        self.assertEqual('2.10', base_compute_client.COMPUTE_MICROVERSION)
        self.assertEqual('3.10', base_client.VOLUME_MICROVERSION)
        self.assertEqual('1.10', base_placement_client.PLACEMENT_MICROVERSION)
