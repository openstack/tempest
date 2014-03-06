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
from tempest.openstack.common import log as logging
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class ServerCfnInitTestJSON(base.BaseOrchestrationTest):
    _interface = 'json'
    existing_keypair = CONF.orchestration.keypair_name is not None

    template = """
HeatTemplateFormatVersion: '2012-12-12'
Description: |
  Template which uses a wait condition to confirm that a minimal
  cfn-init and cfn-signal has worked
Parameters:
  key_name:
    Type: String
  flavor:
    Type: String
  image:
    Type: String
  network:
    Type: String
Resources:
  CfnUser:
    Type: AWS::IAM::User
  SmokeSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Enable only ping and SSH access
      SecurityGroupIngress:
      - {CidrIp: 0.0.0.0/0, FromPort: '-1', IpProtocol: icmp, ToPort: '-1'}
      - {CidrIp: 0.0.0.0/0, FromPort: '22', IpProtocol: tcp, ToPort: '22'}
  SmokeKeys:
    Type: AWS::IAM::AccessKey
    Properties:
      UserName: {Ref: CfnUser}
  SmokeServer:
    Type: OS::Nova::Server
    Metadata:
      AWS::CloudFormation::Init:
        config:
          files:
            /tmp/smoke-status:
              content: smoke test complete
            /etc/cfn/cfn-credentials:
              content:
                Fn::Join:
                - ''
                - - AWSAccessKeyId=
                  - {Ref: SmokeKeys}
                  - '

                    '
                  - AWSSecretKey=
                  - Fn::GetAtt: [SmokeKeys, SecretAccessKey]
                  - '

                    '
              mode: '000400'
              owner: root
              group: root
    Properties:
      image: {Ref: image}
      flavor: {Ref: flavor}
      key_name: {Ref: key_name}
      security_groups:
      - {Ref: SmokeSecurityGroup}
      networks:
      - uuid: {Ref: network}
      user_data:
        Fn::Base64:
          Fn::Join:
          - ''
          - - |-
                #!/bin/bash -v
                /opt/aws/bin/cfn-init
            - |-
                || error_exit ''Failed to run cfn-init''
                /opt/aws/bin/cfn-signal -e 0 --data "`cat /tmp/smoke-status`" '
            - {Ref: WaitHandle}
            - '''

              '
  WaitHandle:
    Type: AWS::CloudFormation::WaitConditionHandle
  WaitCondition:
    Type: AWS::CloudFormation::WaitCondition
    DependsOn: SmokeServer
    Properties:
      Handle: {Ref: WaitHandle}
      Timeout: '600'
Outputs:
  WaitConditionStatus:
    Description: Contents of /tmp/smoke-status on SmokeServer
    Value:
      Fn::GetAtt: [WaitCondition, Data]
  SmokeServerIp:
    Description: IP address of server
    Value:
      Fn::GetAtt: [SmokeServer, first_address]
"""

    @classmethod
    def setUpClass(cls):
        super(ServerCfnInitTestJSON, cls).setUpClass()
        if not CONF.orchestration.image_ref:
            raise cls.skipException("No image available to test")
        cls.client = cls.orchestration_client

        stack_name = data_utils.rand_name('heat')
        if CONF.orchestration.keypair_name:
            keypair_name = CONF.orchestration.keypair_name
        else:
            cls.keypair = cls._create_keypair()
            keypair_name = cls.keypair['name']

        # create the stack
        cls.stack_identifier = cls.create_stack(
            stack_name,
            cls.template,
            parameters={
                'key_name': keypair_name,
                'flavor': CONF.orchestration.instance_type,
                'image': CONF.orchestration.image_ref,
                'network': cls._get_default_network()['id']
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
    def test_stack_wait_condition_data(self):

        sid = self.stack_identifier

        # wait for create to complete.
        self.client.wait_for_stack_status(sid, 'CREATE_COMPLETE')

        # fetch the stack
        resp, body = self.client.get_stack(sid)
        self.assertEqual('CREATE_COMPLETE', body['stack_status'])

        # fetch the stack
        resp, body = self.client.get_stack(sid)
        self.assertEqual('CREATE_COMPLETE', body['stack_status'])

        # This is an assert of great significance, as it means the following
        # has happened:
        # - cfn-init read the provided metadata and wrote out a file
        # - a user was created and credentials written to the server
        # - a cfn-signal was built which was signed with provided credentials
        # - the wait condition was fulfilled and the stack has changed state
        wait_status = json.loads(
            self.stack_output(body, 'WaitConditionStatus'))
        self.assertEqual('smoke test complete', wait_status['00000'])
