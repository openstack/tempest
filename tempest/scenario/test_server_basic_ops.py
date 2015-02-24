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

from tempest import config
from tempest.scenario import manager
from tempest.scenario import utils as test_utils
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)

load_tests = test_utils.load_tests_input_scenario_utils


class TestServerBasicOps(manager.ScenarioTest):

    """
    This smoke test case follows this basic set of operations:

     * Create a keypair for use in launching an instance
     * Create a security group to control network access in instance
     * Add simple permissive rules to the security group
     * Launch an instance
     * Perform ssh to instance
     * Terminate the instance
    """

    def setUp(self):
        super(TestServerBasicOps, self).setUp()
        # Setup image and flavor the test instance
        # Support both configured and injected values
        if not hasattr(self, 'image_ref'):
            self.image_ref = CONF.compute.image_ref
        if not hasattr(self, 'flavor_ref'):
            self.flavor_ref = CONF.compute.flavor_ref
        self.image_utils = test_utils.ImageUtils()
        if not self.image_utils.is_flavor_enough(self.flavor_ref,
                                                 self.image_ref):
            raise self.skipException(
                '{image} does not fit in {flavor}'.format(
                    image=self.image_ref, flavor=self.flavor_ref
                )
            )
        self.run_ssh = CONF.compute.run_ssh and \
            self.image_utils.is_sshable_image(self.image_ref)
        self.ssh_user = self.image_utils.ssh_user(self.image_ref)
        LOG.debug('Starting test for i:{image}, f:{flavor}. '
                  'Run ssh: {ssh}, user: {ssh_user}'.format(
                      image=self.image_ref, flavor=self.flavor_ref,
                      ssh=self.run_ssh, ssh_user=self.ssh_user))

    def add_keypair(self):
        self.keypair = self.create_keypair()

    def boot_instance(self):
        # Create server with image and flavor from input scenario
        security_groups = [{'name': self.security_group['name']}]
        create_kwargs = {
            'key_name': self.keypair['name'],
            'security_groups': security_groups
        }
        self.instance = self.create_server(image=self.image_ref,
                                           flavor=self.flavor_ref,
                                           create_kwargs=create_kwargs)

    def verify_ssh(self):
        if self.run_ssh:
            # Obtain a floating IP
            floating_ip = self.floating_ips_client.create_floating_ip()
            self.addCleanup(self.delete_wrapper,
                            self.floating_ips_client.delete_floating_ip,
                            floating_ip['id'])
            # Attach a floating IP
            self.floating_ips_client.associate_floating_ip_to_server(
                floating_ip['ip'], self.instance['id'])
            # Check ssh
            self.get_remote_client(
                server_or_ip=floating_ip['ip'],
                username=self.image_utils.ssh_user(self.image_ref),
                private_key=self.keypair['private_key'])

    @test.idempotent_id('7fff3fb3-91d8-4fd0-bd7d-0204f1f180ba')
    @test.services('compute', 'network')
    def test_server_basicops(self):
        self.add_keypair()
        self.security_group = self._create_security_group()
        self.boot_instance()
        self.verify_ssh()
        self.servers_client.delete_server(self.instance['id'])
