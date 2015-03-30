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

from oslo_utils import timeutils
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest import config
from tempest import exceptions
import tempest.test

CONF = config.CONF


class BaseTelemetryTest(tempest.test.BaseTestCase):

    """Base test case class for all Telemetry API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseTelemetryTest, cls).skip_checks()
        if not CONF.service_available.ceilometer:
            raise cls.skipException("Ceilometer support is required")

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseTelemetryTest, cls).setup_credentials()
        cls.os = cls.get_client_manager()

    @classmethod
    def setup_clients(cls):
        super(BaseTelemetryTest, cls).setup_clients()
        cls.telemetry_client = cls.os.telemetry_client
        cls.servers_client = cls.os.servers_client
        cls.flavors_client = cls.os.flavors_client
        cls.image_client = cls.os.image_client
        cls.image_client_v2 = cls.os.image_client_v2

    @classmethod
    def resource_setup(cls):
        super(BaseTelemetryTest, cls).resource_setup()
        cls.nova_notifications = ['memory', 'vcpus', 'disk.root.size',
                                  'disk.ephemeral.size']

        cls.glance_notifications = ['image.update', 'image.upload',
                                    'image.delete']

        cls.glance_v2_notifications = ['image.download', 'image.serve']

        cls.server_ids = []
        cls.alarm_ids = []
        cls.image_ids = []

    @classmethod
    def create_alarm(cls, **kwargs):
        body = cls.telemetry_client.create_alarm(
            name=data_utils.rand_name('telemetry_alarm'),
            type='threshold', **kwargs)
        cls.alarm_ids.append(body['alarm_id'])
        return body

    @classmethod
    def create_server(cls):
        body = cls.servers_client.create_server(
            data_utils.rand_name('ceilometer-instance'),
            CONF.compute.image_ref, CONF.compute.flavor_ref,
            wait_until='ACTIVE')
        cls.server_ids.append(body['id'])
        return body

    @classmethod
    def create_image(cls, client):
        body = client.create_image(
            data_utils.rand_name('image'), container_format='bare',
            disk_format='raw', visibility='private')
        cls.image_ids.append(body['id'])
        return body

    @staticmethod
    def cleanup_resources(method, list_of_ids):
        for resource_id in list_of_ids:
            try:
                method(resource_id)
            except lib_exc.NotFound:
                pass

    @classmethod
    def resource_cleanup(cls):
        cls.cleanup_resources(cls.telemetry_client.delete_alarm, cls.alarm_ids)
        cls.cleanup_resources(cls.servers_client.delete_server, cls.server_ids)
        cls.cleanup_resources(cls.image_client.delete_image, cls.image_ids)
        super(BaseTelemetryTest, cls).resource_cleanup()

    def await_samples(self, metric, query):
        """
        This method is to wait for sample to add it to database.
        There are long time delays when using Postgresql (or Mysql)
        database as ceilometer backend
        """
        timeout = CONF.compute.build_timeout
        start = timeutils.utcnow()
        while timeutils.delta_seconds(start, timeutils.utcnow()) < timeout:
            body = self.telemetry_client.list_samples(metric, query)
            if body:
                return body
            time.sleep(CONF.compute.build_interval)

        raise exceptions.TimeoutException(
            'Sample for metric:%s with query:%s has not been added to the '
            'database within %d seconds' % (metric, query,
                                            CONF.compute.build_timeout))
