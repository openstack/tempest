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

from tempest.common import log as logging

from tempest.api.orchestration import base
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr


LOG = logging.getLogger(__name__)


class StacksTestJSON(base.BaseOrchestrationTest):
    _interface = 'json'

    empty_template = "HeatTemplateFormatVersion: '2012-12-12'\n"

    @classmethod
    def setUpClass(cls):
        super(StacksTestJSON, cls).setUpClass()
        cls.client = cls.orchestration_client

    @attr(type='smoke')
    def test_stack_list_responds(self):
        resp, body = self.client.list_stacks()
        stacks = body['stacks']
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(stacks, list)

    @attr(type='smoke')
    def test_stack_crud_no_resources(self):
        stack_name = rand_name('heat')

        # count how many stacks to start with
        resp, body = self.client.list_stacks()

        # create the stack
        stack_identifier = self.create_stack(
            stack_name, self.empty_template)
        stack_id = stack_identifier.split('/')[1]

        # wait for create complete (with no resources it should be instant)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        # check for stack in list
        resp, body = self.client.list_stacks()
        list_ids = list([stack['id'] for stack in body['stacks']])
        self.assertIn(stack_id, list_ids)

        # fetch the stack
        resp, body = self.client.get_stack(stack_identifier)
        self.assertEqual('CREATE_COMPLETE', body['stack_status'])

        # fetch the stack by name
        resp, body = self.client.get_stack(stack_name)
        self.assertEqual('CREATE_COMPLETE', body['stack_status'])

        # fetch the stack by id
        resp, body = self.client.get_stack(stack_id)
        self.assertEqual('CREATE_COMPLETE', body['stack_status'])

        # delete the stack
        resp = self.client.delete_stack(stack_identifier)
        self.assertEqual('204', resp[0]['status'])
