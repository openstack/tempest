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

import time

from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import timeutils
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
        cls.servers_client = os.servers_client
        cls.flavors_client = os.flavors_client

        cls.nova_notifications = ['memory', 'vcpus', 'disk.root.size',
                                  'disk.ephemeral.size']
        cls.server_ids = []
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
    def create_server(cls):
        resp, body = cls.servers_client.create_server(
            data_utils.rand_name('ceilometer-instance'),
            CONF.compute.image_ref, CONF.compute.flavor_ref,
            wait_until='ACTIVE')
        if resp['status'] == '202':
            cls.server_ids.append(body['id'])
        return resp, body

    @staticmethod
    def cleanup_resources(method, list_of_ids):
        for resource_id in list_of_ids:
            try:
                method(resource_id)
            except exceptions.NotFound:
                pass

    @classmethod
    def tearDownClass(cls):
        cls.cleanup_resources(cls.telemetry_client.delete_alarm, cls.alarm_ids)
        cls.cleanup_resources(cls.servers_client.delete_server, cls.server_ids)
        cls.clear_isolated_creds()
        super(BaseTelemetryTest, cls).tearDownClass()

    def await_samples(self, metric, query):
        """
        This method is to wait for sample to add it to database.
        There are long time delays when using Postgresql (or Mysql)
        database as ceilometer backend
        """
        timeout = CONF.compute.build_timeout
        start = timeutils.utcnow()
        while timeutils.delta_seconds(start, timeutils.utcnow()) < timeout:
            resp, body = self.telemetry_client.list_samples(metric, query)
            self.assertEqual(resp.status, 200)
            if body:
                return resp, body
            time.sleep(CONF.compute.build_interval)

        raise exceptions.TimeoutException(
            'Sample for metric:%s with query:%s has not been added to the '
            'database within %d seconds' % (metric, query,
                                            CONF.compute.build_timeout))
