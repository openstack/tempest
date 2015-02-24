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

from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestServerAdvancedOps(manager.ScenarioTest):

    """
    This test case stresses some advanced server instance operations:

     * Resizing an instance
     * Sequence suspend resume
    """

    @classmethod
    def skip_checks(cls):
        super(TestServerAdvancedOps, cls).skip_checks()
        if CONF.compute.flavor_ref_alt == CONF.compute.flavor_ref:
            msg = "Skipping test - flavor_ref and flavor_ref_alt are identical"
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(TestServerAdvancedOps, cls).setup_credentials()

    @test.idempotent_id('e6c28180-7454-4b59-b188-0257af08a63b')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    @test.services('compute')
    def test_resize_server_confirm(self):
        # We create an instance for use in this test
        instance = self.create_server()
        instance_id = instance['id']
        resize_flavor = CONF.compute.flavor_ref_alt
        LOG.debug("Resizing instance %s from flavor %s to flavor %s",
                  instance['id'], instance['flavor']['id'], resize_flavor)
        self.servers_client.resize(instance_id, resize_flavor)
        self.servers_client.wait_for_server_status(instance_id,
                                                   'VERIFY_RESIZE')

        LOG.debug("Confirming resize of instance %s", instance_id)
        self.servers_client.confirm_resize(instance_id)

        self.servers_client.wait_for_server_status(instance_id,
                                                   'ACTIVE')

    @test.idempotent_id('949da7d5-72c8-4808-8802-e3d70df98e2c')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @test.services('compute')
    def test_server_sequence_suspend_resume(self):
        # We create an instance for use in this test
        instance = self.create_server()
        instance_id = instance['id']
        LOG.debug("Suspending instance %s. Current status: %s",
                  instance_id, instance['status'])
        self.servers_client.suspend_server(instance_id)
        self.servers_client.wait_for_server_status(instance_id,
                                                   'SUSPENDED')
        fetched_instance = self.servers_client.get_server(instance_id)
        LOG.debug("Resuming instance %s. Current status: %s",
                  instance_id, fetched_instance['status'])
        self.servers_client.resume_server(instance_id)
        self.servers_client.wait_for_server_status(instance_id,
                                                   'ACTIVE')
        fetched_instance = self.servers_client.get_server(instance_id)
        LOG.debug("Suspending instance %s. Current status: %s",
                  instance_id, fetched_instance['status'])
        self.servers_client.suspend_server(instance_id)
        self.servers_client.wait_for_server_status(instance_id,
                                                   'SUSPENDED')
        fetched_instance = self.servers_client.get_server(instance_id)
        LOG.debug("Resuming instance %s. Current status: %s",
                  instance_id, fetched_instance['status'])
        self.servers_client.resume_server(instance_id)
        self.servers_client.wait_for_server_status(instance_id,
                                                   'ACTIVE')
