# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import logging

from tempest.api.orchestration import base
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr


LOG = logging.getLogger(__name__)


class InstanceCfnInitTestJSON(base.BaseOrchestrationTest):
    _interface = 'json'

    template = """
HeatTemplateFormatVersion: '2012-12-12'
Description: |
  Template which uses a wait condition to confirm that a minimal
  cfn-init and cfn-signal has worked
Parameters:
  KeyName:
    Type: String
  InstanceType:
    Type: String
  ImageId:
    Type: String
Resources:
  CfnUser:
    Type: AWS::IAM::User
  SmokeKeys:
    Type: AWS::IAM::AccessKey
    Properties:
      UserName: {Ref: CfnUser}
  SmokeServer:
    Type: AWS::EC2::Instance
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
      ImageId: {Ref: ImageId}
      InstanceType: {Ref: InstanceType}
      KeyName: {Ref: KeyName}
      UserData:
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
"""

    @classmethod
    def setUpClass(cls):
        super(InstanceCfnInitTestJSON, cls).setUpClass()
        if not cls.orchestration_cfg.image_ref:
            raise cls.skipException("No image available to test")
        cls.client = cls.orchestration_client

    def setUp(self):
        super(InstanceCfnInitTestJSON, self).setUp()
        stack_name = rand_name('heat')
        keypair_name = (self.orchestration_cfg.keypair_name or
                        self._create_keypair()['name'])

        # create the stack
        self.stack_identifier = self.create_stack(
            stack_name,
            self.template,
            parameters={
                'KeyName': keypair_name,
                'InstanceType': self.orchestration_cfg.instance_type,
                'ImageId': self.orchestration_cfg.image_ref
            })

    @attr(type='gate')
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
        # - a user was created and credentials written to the instance
        # - a cfn-signal was built which was signed with provided credentials
        # - the wait condition was fulfilled and the stack has changed state
        wait_status = json.loads(body['outputs'][0]['output_value'])
        self.assertEqual('smoke test complete', wait_status['00000'])
