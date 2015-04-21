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

from tempest_lib.common.utils import data_utils

from tempest.api.orchestration import base
from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class StacksTestJSON(base.BaseOrchestrationTest):

    @classmethod
    def resource_setup(cls):
        super(StacksTestJSON, cls).resource_setup()
        cls.stack_name = data_utils.rand_name('heat')
        template = cls.read_template('non_empty_stack')
        image_id = (CONF.compute.image_ref or
                    cls._create_image()['id'])
        flavor = CONF.orchestration.instance_type
        # create the stack
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            template,
            parameters={
                'trigger': 'start',
                'image': image_id,
                'flavor': flavor
            })
        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.resource_name = 'fluffy'
        cls.resource_type = 'AWS::AutoScaling::LaunchConfiguration'
        cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')

    def _list_stacks(self, expected_num=None, **filter_kwargs):
        stacks = self.client.list_stacks(params=filter_kwargs)
        self.assertIsInstance(stacks, list)
        if expected_num is not None:
            self.assertEqual(expected_num, len(stacks))
        return stacks

    @test.attr(type='gate')
    @test.idempotent_id('065c652a-720d-4760-9132-06aedeb8e3ab')
    def test_stack_list(self):
        """Created stack should be in the list of existing stacks."""
        stacks = self._list_stacks()
        stacks_names = map(lambda stack: stack['stack_name'], stacks)
        self.assertIn(self.stack_name, stacks_names)

    @test.attr(type='gate')
    @test.idempotent_id('992f96e3-41ee-4ff6-91c7-bcfb670c0919')
    def test_stack_show(self):
        """Getting details about created stack should be possible."""
        stack = self.client.show_stack(self.stack_name)
        self.assertIsInstance(stack, dict)
        self.assert_fields_in_dict(stack, 'stack_name', 'id', 'links',
                                   'parameters', 'outputs', 'disable_rollback',
                                   'stack_status_reason', 'stack_status',
                                   'creation_time', 'updated_time',
                                   'capabilities', 'notification_topics',
                                   'timeout_mins', 'template_description')
        self.assert_fields_in_dict(stack['parameters'], 'AWS::StackId',
                                   'trigger', 'AWS::Region', 'AWS::StackName')
        self.assertEqual(True, stack['disable_rollback'],
                         'disable_rollback should default to True')
        self.assertEqual(self.stack_name, stack['stack_name'])
        self.assertEqual(self.stack_id, stack['id'])
        self.assertEqual('fluffy', stack['outputs'][0]['output_key'])

    @test.attr(type='gate')
    @test.idempotent_id('fe719f7a-305a-44d8-bbb5-c91e93d9da17')
    def test_suspend_resume_stack(self):
        """Suspend and resume a stack."""
        self.client.suspend_stack(self.stack_identifier)
        self.client.wait_for_stack_status(self.stack_identifier,
                                          'SUSPEND_COMPLETE')
        self.client.resume_stack(self.stack_identifier)
        self.client.wait_for_stack_status(self.stack_identifier,
                                          'RESUME_COMPLETE')

    @test.attr(type='gate')
    @test.idempotent_id('c951d55e-7cce-4c1f-83a0-bad735437fa6')
    def test_list_resources(self):
        """Getting list of created resources for the stack should be possible.
        """
        resources = self.list_resources(self.stack_identifier)
        self.assertEqual({self.resource_name: self.resource_type}, resources)

    @test.attr(type='gate')
    @test.idempotent_id('2aba03b3-392f-4237-900b-1f5a5e9bd962')
    def test_show_resource(self):
        """Getting details about created resource should be possible."""
        resource = self.client.show_resource(self.stack_identifier,
                                             self.resource_name)
        self.assertIsInstance(resource, dict)
        self.assert_fields_in_dict(resource, 'resource_name', 'description',
                                   'links', 'logical_resource_id',
                                   'resource_status', 'updated_time',
                                   'required_by', 'resource_status_reason',
                                   'physical_resource_id', 'resource_type')
        self.assertEqual(self.resource_name, resource['logical_resource_id'])
        self.assertEqual(self.resource_type, resource['resource_type'])

    @test.attr(type='gate')
    @test.idempotent_id('898070a9-eba5-4fae-b7d6-cf3ffa03090f')
    def test_resource_metadata(self):
        """Getting metadata for created resources should be possible."""
        metadata = self.client.show_resource_metadata(
            self.stack_identifier,
            self.resource_name)
        self.assertIsInstance(metadata, dict)
        self.assertEqual(['Tom', 'Stinky'], metadata.get('kittens', None))

    @test.attr(type='gate')
    @test.idempotent_id('46567533-0a7f-483b-8942-fa19e0f17839')
    def test_list_events(self):
        """Getting list of created events for the stack should be possible."""
        events = self.client.list_events(self.stack_identifier)
        self.assertIsInstance(events, list)

        for event in events:
            self.assert_fields_in_dict(event, 'logical_resource_id', 'id',
                                       'resource_status_reason',
                                       'resource_status', 'event_time')

        resource_statuses = map(lambda event: event['resource_status'], events)
        self.assertIn('CREATE_IN_PROGRESS', resource_statuses)
        self.assertIn('CREATE_COMPLETE', resource_statuses)

    @test.attr(type='gate')
    @test.idempotent_id('92465723-1673-400a-909d-4773757a3f21')
    def test_show_event(self):
        """Getting details about an event should be possible."""
        events = self.client.list_resource_events(self.stack_identifier,
                                                  self.resource_name)
        self.assertNotEqual([], events)
        events.sort(key=lambda event: event['event_time'])
        event_id = events[0]['id']
        event = self.client.show_event(self.stack_identifier,
                                       self.resource_name, event_id)
        self.assertIsInstance(event, dict)
        self.assert_fields_in_dict(event, 'resource_name', 'event_time',
                                   'links', 'logical_resource_id',
                                   'resource_status', 'resource_status_reason',
                                   'physical_resource_id', 'id',
                                   'resource_properties', 'resource_type')
        self.assertEqual(self.resource_name, event['resource_name'])
        self.assertEqual('state changed', event['resource_status_reason'])
        self.assertEqual(self.resource_name, event['logical_resource_id'])
