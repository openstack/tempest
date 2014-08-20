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

from tempest.api.telemetry import base
from tempest import config
from tempest import test

CONF = config.CONF


class TelemetryNotificationAPITestJSON(base.BaseTelemetryTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        if CONF.telemetry.too_slow_to_test:
            raise cls.skipException("Ceilometer feature for fast work mysql "
                                    "is disabled")
        super(TelemetryNotificationAPITestJSON, cls).setUpClass()

    @test.attr(type="gate")
    @testtools.skipIf(not CONF.service_available.nova,
                      "Nova is not available.")
    @test.skip_because(bug="1336755")
    def test_check_nova_notification(self):

        resp, body = self.create_server()
        self.assertEqual(resp.status, 202)

        query = ('resource', 'eq', body['id'])

        for metric in self.nova_notifications:
            self.await_samples(metric, query)

    @test.attr(type="smoke")
    @test.services("image")
    @testtools.skipIf(not CONF.image_feature_enabled.api_v1,
                      "Glance api v1 is disabled")
    @test.skip_because(bug='1351627')
    def test_check_glance_v1_notifications(self):
        _, body = self.create_image(self.image_client)
        self.image_client.update_image(body['id'], data='data')

        query = 'resource', 'eq', body['id']

        self.image_client.delete_image(body['id'])

        for metric in self.glance_notifications:
            self.await_samples(metric, query)

    @test.attr(type="smoke")
    @test.services("image")
    @testtools.skipIf(not CONF.image_feature_enabled.api_v2,
                      "Glance api v2 is disabled")
    @test.skip_because(bug='1351627')
    def test_check_glance_v2_notifications(self):
        _, body = self.create_image(self.image_client_v2)

        self.image_client_v2.store_image(body['id'], "file")
        self.image_client_v2.get_image_file(body['id'])

        query = 'resource', 'eq', body['id']

        for metric in self.glance_v2_notifications:
            self.await_samples(metric, query)


class TelemetryNotificationAPITestXML(TelemetryNotificationAPITestJSON):
    _interface = 'xml'
