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

from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
import tempest.test

CONF = config.CONF


class BaseTelemetryTest(tempest.test.BaseTestCase):

    """Base test case class for all Telemetry API tests."""

    @classmethod
    def setUpClass(cls):
        if not CONF.service_available.ceilometer:
            raise cls.skipException("Ceilometer support is required")
        super(BaseTelemetryTest, cls).setUpClass()
        os = cls.get_client_manager()
        cls.telemetry_client = os.telemetry_client
        cls.alarm_ids = []

    @classmethod
    def create_alarm(cls, **kwargs):
        resp, body = cls.telemetry_client.create_alarm(
            name=data_utils.rand_name('telemetry_alarm'),
            type='threshold', **kwargs)
        if resp['status'] == '201':
            cls.alarm_ids.append(body['alarm_id'])
        return resp, body

    @classmethod
    def tearDownClass(cls):
        for alarm_id in cls.alarm_ids:
            try:
                cls.telemetry_client.delete_alarm(alarm_id)
            except exceptions.NotFound:
                pass
        cls.clear_isolated_creds()
        super(BaseTelemetryTest, cls).tearDownClass()
