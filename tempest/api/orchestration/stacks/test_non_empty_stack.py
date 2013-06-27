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

import logging

from tempest.api.orchestration import base
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr


LOG = logging.getLogger(__name__)


class StacksTestJSON(base.BaseOrchestrationTest):
    _interface = 'json'

    template = """
HeatTemplateFormatVersion: '2012-12-12'
Description: |
  Template which creates single EC2 instance
Parameters:
  KeyName:
    Type: String
  InstanceType:
    Type: String
  ImageId:
    Type: String
Resources:
  SmokeServer:
    Type: AWS::EC2::Instance
    Metadata:
      Name: SmokeServer
    Properties:
      ImageId: {Ref: ImageId}
      InstanceType: {Ref: InstanceType}
      KeyName: {Ref: KeyName}
      UserData:
        Fn::Base64:
          Fn::Join:
          - ''
          - - '#!/bin/bash -v

              '
            - /opt/aws/bin/cfn-signal -e 0 -r "SmokeServer created" '
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
"""

    @classmethod
    def setUpClass(cls):
        super(StacksTestJSON, cls).setUpClass()
        if not cls.orchestration_cfg.image_ref:
            raise cls.skipException("No image available to test")
        cls.client = cls.orchestration_client
        cls.stack_name = rand_name('heat')
        keypair_name = (cls.orchestration_cfg.keypair_name or
                        cls._create_keypair()['name'])

        # create the stack
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            cls.template,
            parameters={
                'KeyName': keypair_name,
                'InstanceType': cls.orchestration_cfg.instance_type,
                'ImageId': cls.orchestration_cfg.image_ref
            })
        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.resource_name = 'SmokeServer'
        cls.resource_type = 'AWS::EC2::Instance'
        cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')

    @attr(type='slow')
    def test_stack_list(self):
        """Created stack should be on the list of existing stacks."""
        resp, stacks = self.client.list_stacks()
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(stacks, list)
        stacks_names = map(lambda stack: stack['stack_name'], stacks)
        self.assertIn(self.stack_name, stacks_names)

    @attr(type='slow')
    def test_stack_show(self):
        """Getting details about created stack should be possible."""
        resp, stack = self.client.get_stack(self.stack_name)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(stack, dict)
        self.assertEqual(self.stack_name, stack['stack_name'])
        self.assertEqual(self.stack_id, stack['id'])

    @attr(type='slow')
    def test_list_resources(self):
        """Getting list of created resources for the stack should be possible.
        """
        resp, resources = self.client.list_resources(self.stack_identifier)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(resources, list)
        resources_names = map(lambda resource: resource['logical_resource_id'],
                              resources)
        self.assertIn(self.resource_name, resources_names)
        resources_types = map(lambda resource: resource['resource_type'],
                              resources)
        self.assertIn(self.resource_type, resources_types)

    @attr(type='slow')
    def test_show_resource(self):
        """Getting details about created resource should be possible."""
        resp, resource = self.client.get_resource(self.stack_identifier,
                                                  self.resource_name)
        self.assertIsInstance(resource, dict)
        self.assertEqual(self.resource_name, resource['logical_resource_id'])
        self.assertEqual(self.resource_type, resource['resource_type'])

    @attr(type='slow')
    def test_resource_metadata(self):
        """Getting metadata for created resource should be possible."""
        resp, metadata = self.client.show_resource_metadata(
            self.stack_identifier,
            self.resource_name)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(metadata, dict)
        self.assertEqual(self.resource_name, metadata.get('Name', None))

    @attr(type='slow')
    def test_list_events(self):
        """Getting list of created events for the stack should be possible."""
        resp, events = self.client.list_events(self.stack_identifier)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(events, list)
        resource_statuses = map(lambda event: event['resource_status'], events)
        self.assertIn('CREATE_IN_PROGRESS', resource_statuses)
        self.assertIn('CREATE_COMPLETE', resource_statuses)

    @attr(type='slow')
    def test_show_event(self):
        """Getting details about existing event should be possible."""
        resp, events = self.client.list_resource_events(self.stack_identifier,
                                                        self.resource_name)
        self.assertNotEqual([], events)
        events.sort(key=lambda event: event['event_time'])
        event_id = events[0]['id']
        resp, event = self.client.show_event(self.stack_identifier,
                                             self.resource_name, event_id)
        self.assertEqual('200', resp['status'])
        self.assertEqual('CREATE_IN_PROGRESS', event['resource_status'])
        self.assertEqual('state changed', event['resource_status_reason'])
        self.assertEqual(self.resource_name, event['logical_resource_id'])
        self.assertIsInstance(event, dict)
