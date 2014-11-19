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

import json

from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class CfnInitScenarioTest(manager.OrchestrationScenarioTest):

    def setUp(self):
        super(CfnInitScenarioTest, self).setUp()
        if not CONF.orchestration.image_ref:
            raise self.skipException("No image available to test")
        self.client = self.orchestration_client
        self.template_name = 'cfn_init_signal.yaml'

    def assign_keypair(self):
        self.stack_name = self._stack_rand_name()
        if CONF.orchestration.keypair_name:
            self.keypair = None
            self.keypair_name = CONF.orchestration.keypair_name
        else:
            self.keypair = self.create_keypair()
            self.keypair_name = self.keypair['name']

    def launch_stack(self):
        net = self._get_default_network()
        self.parameters = {
            'key_name': self.keypair_name,
            'flavor': CONF.orchestration.instance_type,
            'image': CONF.orchestration.image_ref,
            'timeout': CONF.orchestration.build_timeout,
            'network': net['id'],
        }

        # create the stack
        self.template = self._load_template(__file__, self.template_name)
        _, stack = self.client.create_stack(
            name=self.stack_name,
            template=self.template,
            parameters=self.parameters)
        stack = stack['stack']

        _, self.stack = self.client.get_stack(stack['id'])
        self.stack_identifier = '%s/%s' % (self.stack_name, self.stack['id'])
        self.addCleanup(self.delete_wrapper,
                        self.orchestration_client.delete_stack,
                        self.stack_identifier)

    def check_stack(self):
        sid = self.stack_identifier
        self.client.wait_for_resource_status(
            sid, 'WaitHandle', 'CREATE_COMPLETE')
        self.client.wait_for_resource_status(
            sid, 'SmokeSecurityGroup', 'CREATE_COMPLETE')
        self.client.wait_for_resource_status(
            sid, 'SmokeKeys', 'CREATE_COMPLETE')
        self.client.wait_for_resource_status(
            sid, 'CfnUser', 'CREATE_COMPLETE')
        self.client.wait_for_resource_status(
            sid, 'SmokeServer', 'CREATE_COMPLETE')

        _, server_resource = self.client.get_resource(sid, 'SmokeServer')
        server_id = server_resource['physical_resource_id']
        _, server = self.servers_client.get_server(server_id)
        server_ip =\
            server['addresses'][CONF.compute.network_for_ssh][0]['addr']

        if not self.ping_ip_address(
            server_ip, ping_timeout=CONF.orchestration.build_timeout):
            self._log_console_output(servers=[server])
            self.fail(
                "(CfnInitScenarioTest:test_server_cfn_init) Timed out waiting "
                "for %s to become reachable" % server_ip)

        try:
            self.client.wait_for_resource_status(
                sid, 'WaitCondition', 'CREATE_COMPLETE')
        except (exceptions.StackResourceBuildErrorException,
                exceptions.TimeoutException) as e:
            raise e
        finally:
            # attempt to log the server console regardless of WaitCondition
            # going to complete. This allows successful and failed cloud-init
            # logs to be compared
            self._log_console_output(servers=[server])

        self.client.wait_for_stack_status(sid, 'CREATE_COMPLETE')

        _, stack = self.client.get_stack(sid)

        # This is an assert of great significance, as it means the following
        # has happened:
        # - cfn-init read the provided metadata and wrote out a file
        # - a user was created and credentials written to the server
        # - a cfn-signal was built which was signed with provided credentials
        # - the wait condition was fulfilled and the stack has changed state
        wait_status = json.loads(
            self._stack_output(stack, 'WaitConditionStatus'))
        self.assertEqual('smoke test complete', wait_status['smoke_status'])

        if self.keypair:
            # Check that the user can authenticate with the generated
            # keypair
            try:
                linux_client = self.get_remote_client(
                    server_ip, username='ec2-user')
                linux_client.validate_authentication()
            except (exceptions.ServerUnreachable,
                    exceptions.SSHTimeout) as e:
                self._log_console_output(servers=[server])
                raise e

    @test.attr(type='slow')
    @test.skip_because(bug='1374175')
    @test.services('orchestration', 'compute')
    def test_server_cfn_init(self):
        self.assign_keypair()
        self.launch_stack()
        self.check_stack()
