# Copyright 2013 OpenStack Foundation
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

from oslo_log import log as logging

from tempest import cli
from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyCeilometerClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Ceilometer CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def resource_setup(cls):
        if (not CONF.service_available.ceilometer):
            msg = ("Skipping all Ceilometer cli tests because it is "
                   "not available")
            raise cls.skipException(msg)
        super(SimpleReadOnlyCeilometerClientTest, cls).resource_setup()

    def ceilometer(self, *args, **kwargs):
        return self.clients.ceilometer(
            *args, endpoint_type=CONF.telemetry.endpoint_type, **kwargs)

    @test.idempotent_id('ab717d43-a9c4-4dcf-bad8-c4777933a970')
    def test_ceilometer_meter_list(self):
        self.ceilometer('meter-list')

    @test.attr(type='slow')
    @test.idempotent_id('fe2e52a4-a99b-426e-a52d-d0bde50f3e4c')
    def test_ceilometer_resource_list(self):
        self.ceilometer('resource-list')

    @test.idempotent_id('eede695c-f3bf-449f-a420-02f3cc426d52')
    def test_ceilometermeter_alarm_list(self):
        self.ceilometer('alarm-list')

    @test.idempotent_id('0586bcc4-8e35-415f-8f23-77b590042684')
    def test_ceilometer_version(self):
        self.ceilometer('', flags='--version')
