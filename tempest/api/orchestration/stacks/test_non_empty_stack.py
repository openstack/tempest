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
from tempest.common.utils import data_utils
from tempest import test


LOG = logging.getLogger(__name__)


class StacksTestJSON(base.BaseOrchestrationTest):

    @classmethod
    def setUpClass(cls):
        super(StacksTestJSON, cls).setUpClass()
        cls.stack_name = data_utils.rand_name('heat')
        template = cls.load_template('non_empty_stack')

        # create the stack
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            template,
            parameters={
                'trigger': 'start'
            })
        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.resource_name = 'fluffy'
        cls.resource_type = 'AWS::AutoScaling::LaunchConfiguration'
        cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')

    def _list_stacks(self, expected_num=None, **filter_kwargs):
        resp, stacks = self.client.list_stacks(params=filter_kwargs)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(stacks, list)
        if expected_num is not None:
            self.assertEqual(expected_num, len(stacks))
        return stacks

    @test.attr(type='gate')
    def test_stack_list(self):
        """Created stack should be in the list of existing stacks."""
        stacks = self._list_stacks()
        stacks_names = map(lambda stack: stack['stack_name'], stacks)
        self.assertIn(self.stack_name, stacks_names)

    @test.attr(type='gate')
    def test_stack_show(self):
        """Getting details about created stack should be possible."""
        resp, stack = self.client.get_stack(self.stack_name)
        self.assertEqual('200', resp['status'])
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
    def test_suspend_resume_stack(self):
        """Suspend and resume a stack."""
        resp, suspend_stack = self.client.suspend_stack(self.stack_identifier)
        self.assertEqual('200', resp['status'])
        self.client.wait_for_stack_status(self.stack_identifier,
                                          'SUSPEND_COMPLETE')
        resp, resume_stack = self.client.resume_stack(self.stack_identifier)
        self.assertEqual('200', resp['status'])
        self.client.wait_for_stack_status(self.stack_identifier,
                                          'RESUME_COMPLETE')

    @test.attr(type='gate')
    def test_list_resources(self):
        """Getting list of created resources for the stack should be possible.
        """
        resources = self.list_resources(self.stack_identifier)
        self.assertEqual({self.resource_name: self.resource_type}, resources)

    @test.attr(type='gate')
    def test_show_resource(self):
        """Getting details about created resource should be possible."""
        resp, resource = self.client.get_resource(self.stack_identifier,
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
    def test_resource_metadata(self):
        """Getting metadata for created resources should be possible."""
        resp, metadata = self.client.show_resource_metadata(
            self.stack_identifier,
            self.resource_name)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(metadata, dict)
        self.assertEqual(['Tom', 'Stinky'], metadata.get('kittens', None))

    @test.attr(type='gate')
    def test_list_events(self):
        """Getting list of created events for the stack should be possible."""
        resp, events = self.client.list_events(self.stack_identifier)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(events, list)

        for event in events:
            self.assert_fields_in_dict(event, 'logical_resource_id', 'id',
                                       'resource_status_reason',
                                       'resource_status', 'event_time')

        resource_statuses = map(lambda event: event['resource_status'], events)
        self.assertIn('CREATE_IN_PROGRESS', resource_statuses)
        self.assertIn('CREATE_COMPLETE', resource_statuses)

    @test.attr(type='gate')
    def test_show_event(self):
        """Getting details about an event should be possible."""
        resp, events = self.client.list_resource_events(self.stack_identifier,
                                                        self.resource_name)
        self.assertNotEqual([], events)
        events.sort(key=lambda event: event['event_time'])
        event_id = events[0]['id']
        resp, event = self.client.show_event(self.stack_identifier,
                                             self.resource_name, event_id)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(event, dict)
        self.assert_fields_in_dict(event, 'resource_name', 'event_time',
                                   'links', 'logical_resource_id',
                                   'resource_status', 'resource_status_reason',
                                   'physical_resource_id', 'id',
                                   'resource_properties', 'resource_type')
        self.assertEqual(self.resource_name, event['resource_name'])
        self.assertEqual('state changed', event['resource_status_reason'])
        self.assertEqual(self.resource_name, event['logical_resource_id'])
