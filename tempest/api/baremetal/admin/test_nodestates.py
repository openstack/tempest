# Copyright 2014 NEC Corporation.  All rights reserved.
#
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

from tempest.api.baremetal.admin import base
from tempest import exceptions
from tempest.openstack.common import timeutils
from tempest import test


class TestNodeStates(base.BaseBaremetalTest):
    """Tests for baremetal NodeStates."""

    @classmethod
    def setUpClass(cls):
        super(TestNodeStates, cls).setUpClass()
        _, cls.chassis = cls.create_chassis()
        _, cls.node = cls.create_node(cls.chassis['uuid'])

    def _validate_power_state(self, node_uuid, power_state):
        # Validate that power state is set within timeout
        if power_state == 'rebooting':
            power_state = 'power on'
        start = timeutils.utcnow()
        while timeutils.delta_seconds(
                start, timeutils.utcnow()) < self.power_timeout:
            _, node = self.client.show_node(node_uuid)
            if node['power_state'] == power_state:
                return
        message = ('Failed to set power state within '
                   'the required time: %s sec.' % self.power_timeout)
        raise exceptions.TimeoutException(message)

    @test.attr(type='smoke')
    def test_list_nodestates(self):
        _, nodestates = self.client.list_nodestates(self.node['uuid'])
        for key in nodestates:
            self.assertEqual(nodestates[key], self.node[key])

    @test.attr(type='smoke')
    def test_set_node_power_state(self):
        _, node = self.create_node(self.chassis['uuid'])
        states = ["power on", "rebooting", "power off"]
        for state in states:
            # Set power state
            self.client.set_node_power_state(node['uuid'], state)
            # Check power state after state is set
            self._validate_power_state(node['uuid'], state)
