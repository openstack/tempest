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

import time

from tempest.scenario import manager
from tempest.test import attr
from tempest.test import call_until_true


class AutoScalingTest(manager.OrchestrationScenarioTest):

    def setUp(self):
        super(AutoScalingTest, self).setUp()
        if not self.config.orchestration.image_ref:
            raise self.skipException("No image available to test")
        self.client = self.orchestration_client

    def assign_keypair(self):
        self.stack_name = self._stack_rand_name()
        if self.config.orchestration.keypair_name:
            self.keypair_name = self.config.orchestration.keypair_name
        else:
            self.keypair = self.create_keypair()
            self.keypair_name = self.keypair.id

    def launch_stack(self):
        self.parameters = {
            'KeyName': self.keypair_name,
            'InstanceType': self.config.orchestration.instance_type,
            'ImageId': self.config.orchestration.image_ref,
            'StackStart': str(time.time())
        }

        # create the stack
        self.template = self._load_template(__file__, 'test_autoscaling.yaml')
        self.client.stacks.create(
            stack_name=self.stack_name,
            template=self.template,
            parameters=self.parameters)

        self.stack = self.client.stacks.get(self.stack_name)
        self.stack_identifier = '%s/%s' % (self.stack_name, self.stack.id)

        # if a keypair was set, do not delete the stack on exit to allow
        # for manual post-mortums
        if not self.config.orchestration.keypair_name:
            self.set_resource('stack', self.stack)

    @attr(type='slow')
    def test_scale_up_then_down(self):

        self.assign_keypair()
        self.launch_stack()

        sid = self.stack_identifier
        timeout = self.config.orchestration.build_timeout
        interval = 10

        self.assertEqual('CREATE', self.stack.action)
        # wait for create to complete.
        self.status_timeout(self.client.stacks, sid, 'COMPLETE')

        self.stack.get()
        self.assertEqual('CREATE_COMPLETE', self.stack.stack_status)

        # the resource SmokeServerGroup is implemented as a nested
        # stack, so servers can be counted by counting the resources
        # inside that nested stack
        resource = self.client.resources.get(sid, 'SmokeServerGroup')
        nested_stack_id = resource.physical_resource_id

        def server_count():
            # the number of servers is the number of resources
            # in the nexted stack
            self.server_count = len(
                self.client.resources.list(nested_stack_id))
            return self.server_count

        def assertScale(from_servers, to_servers):
            call_until_true(lambda: server_count() == to_servers,
                            timeout, interval)
            self.assertEqual(to_servers, self.server_count,
                             'Failed scaling from %d to %d servers' % (
                                 from_servers, to_servers))

        # he marched them up to the top of the hill
        assertScale(1, 2)
        assertScale(2, 3)

        # and he marched them down again
        assertScale(3, 2)
        assertScale(2, 1)
