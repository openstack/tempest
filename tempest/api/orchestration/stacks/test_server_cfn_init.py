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
import testtools

from tempest.api.orchestration import base
from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class ServerCfnInitTestJSON(base.BaseOrchestrationTest):
    existing_keypair = CONF.orchestration.keypair_name is not None

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(ServerCfnInitTestJSON, cls).setUpClass()
        if not CONF.orchestration.image_ref:
            raise cls.skipException("No image available to test")
        template = cls.load_template('cfn_init_signal')
        stack_name = data_utils.rand_name('heat')
        if CONF.orchestration.keypair_name:
            keypair_name = CONF.orchestration.keypair_name
        else:
            cls.keypair = cls._create_keypair()
            keypair_name = cls.keypair['name']

        # create the stack
        cls.stack_identifier = cls.create_stack(
            stack_name,
            template,
            parameters={
                'key_name': keypair_name,
                'flavor': CONF.orchestration.instance_type,
                'image': CONF.orchestration.image_ref,
                'network': cls._get_default_network()['id'],
                'timeout': CONF.orchestration.build_timeout
            })

    @test.attr(type='slow')
    @testtools.skipIf(existing_keypair, 'Server ssh tests are disabled.')
    def test_can_log_into_created_server(self):

        sid = self.stack_identifier
        rid = 'SmokeServer'

        # wait for create to complete.
        self.client.wait_for_stack_status(sid, 'CREATE_COMPLETE')

        resp, body = self.client.get_resource(sid, rid)
        self.assertEqual('CREATE_COMPLETE', body['resource_status'])

        # fetch the IP address from servers client, since we can't get it
        # from the stack until stack create is complete
        resp, server = self.servers_client.get_server(
            body['physical_resource_id'])

        # Check that the user can authenticate with the generated password
        linux_client = remote_client.RemoteClient(server, 'ec2-user',
                                                  pkey=self.keypair[
                                                      'private_key'])
        linux_client.validate_authentication()

    @test.attr(type='slow')
    def test_all_resources_created(self):
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
        try:
            self.client.wait_for_resource_status(
                sid, 'WaitCondition', 'CREATE_COMPLETE')
        except (exceptions.StackResourceBuildErrorException,
                exceptions.TimeoutException) as e:
            # attempt to log the server console to help with debugging
            # the cause of the server not signalling the waitcondition
            # to heat.
            resp, body = self.client.get_resource(sid, 'SmokeServer')
            server_id = body['physical_resource_id']
            LOG.debug('Console output for %s', server_id)
            resp, output = self.servers_client.get_console_output(
                server_id, None)
            LOG.debug(output)
            raise e

        # wait for create to complete.
        self.client.wait_for_stack_status(sid, 'CREATE_COMPLETE')

        # This is an assert of great significance, as it means the following
        # has happened:
        # - cfn-init read the provided metadata and wrote out a file
        # - a user was created and credentials written to the server
        # - a cfn-signal was built which was signed with provided credentials
        # - the wait condition was fulfilled and the stack has changed state
        wait_status = json.loads(
            self.get_stack_output(sid, 'WaitConditionStatus'))
        self.assertEqual('smoke test complete', wait_status['00000'])
