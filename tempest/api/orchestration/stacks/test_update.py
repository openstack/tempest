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
from tempest.test import attr


LOG = logging.getLogger(__name__)


class UpdateStackTestJSON(base.BaseOrchestrationTest):
    _interface = 'json'

    template = '''
heat_template_version: 2013-05-23
resources:
  random1:
    type: OS::Heat::RandomString
'''
    update_template = '''
heat_template_version: 2013-05-23
resources:
  random1:
    type: OS::Heat::RandomString
  random2:
    type: OS::Heat::RandomString
'''

    def update_stack(self, stack_identifier, template):
        stack_name = stack_identifier.split('/')[0]
        resp = self.client.update_stack(
            stack_identifier=stack_identifier,
            name=stack_name,
            template=template)
        self.assertEqual('202', resp[0]['status'])
        self.client.wait_for_stack_status(stack_identifier, 'UPDATE_COMPLETE')

    @attr(type='gate')
    def test_stack_update_nochange(self):
        stack_name = data_utils.rand_name('heat')
        stack_identifier = self.create_stack(stack_name, self.template)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')
        expected_resources = {'random1': 'OS::Heat::RandomString'}
        self.assertEqual(expected_resources,
                         self.list_resources(stack_identifier))

        # Update with no changes, resources should be unchanged
        self.update_stack(stack_identifier, self.template)
        self.assertEqual(expected_resources,
                         self.list_resources(stack_identifier))

    @attr(type='gate')
    def test_stack_update_add_remove(self):
        stack_name = data_utils.rand_name('heat')
        stack_identifier = self.create_stack(stack_name, self.template)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')
        initial_resources = {'random1': 'OS::Heat::RandomString'}
        self.assertEqual(initial_resources,
                         self.list_resources(stack_identifier))

        # Add one resource via a stack update
        self.update_stack(stack_identifier, self.update_template)
        updated_resources = {'random1': 'OS::Heat::RandomString',
                             'random2': 'OS::Heat::RandomString'}
        self.assertEqual(updated_resources,
                         self.list_resources(stack_identifier))

        # Then remove it by updating with the original template
        self.update_stack(stack_identifier, self.template)
        self.assertEqual(initial_resources,
                         self.list_resources(stack_identifier))
