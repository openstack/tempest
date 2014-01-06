# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from oslo.config import cfg

import tempest.cli
from tempest.openstack.common import log as logging

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyCeilometerClientTest(tempest.cli.ClientTestBase):
    """Basic, read-only tests for Ceilometer CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def setUpClass(cls):
        if (not CONF.service_available.ceilometer):
            msg = ("Skipping all Ceilometer cli tests because it is "
                   "not available")
            raise cls.skipException(msg)
        super(SimpleReadOnlyCeilometerClientTest, cls).setUpClass()

    def test_ceilometer_meter_list(self):
        self.ceilometer('meter-list')

    def test_ceilometer_resource_list(self):
        self.ceilometer('resource-list')

    def test_ceilometermeter_alarm_list(self):
        self.ceilometer('alarm-list')

    def test_ceilometer_version(self):
        self.ceilometer('', flags='--version')
