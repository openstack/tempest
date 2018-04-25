# Copyright 2012 OpenStack Foundation
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
import testtools

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestServerAdvancedOps(manager.ScenarioTest):

    """The test suite for server advanced operations

    This test case stresses some advanced server instance operations:
     * Sequence suspend resume
    """

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(TestServerAdvancedOps, cls).setup_credentials()

    @decorators.attr(type='slow')
    @decorators.idempotent_id('949da7d5-72c8-4808-8802-e3d70df98e2c')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @utils.services('compute')
    def test_server_sequence_suspend_resume(self):
        # We create an instance for use in this test
        instance_id = self.create_server()['id']

        for _ in range(2):
            LOG.debug("Suspending instance %s", instance_id)
            self.servers_client.suspend_server(instance_id)
            waiters.wait_for_server_status(self.servers_client, instance_id,
                                           'SUSPENDED')

            LOG.debug("Resuming instance %s", instance_id)
            self.servers_client.resume_server(instance_id)
            waiters.wait_for_server_status(self.servers_client, instance_id,
                                           'ACTIVE')
