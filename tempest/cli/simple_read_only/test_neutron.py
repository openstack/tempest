# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
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

import re
import subprocess

from oslo.config import cfg
import testtools

import tempest.cli
from tempest.openstack.common import log as logging

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyNeutronClientTest(tempest.cli.ClientTestBase):
    """Basic, read-only tests for Neutron CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """
    if (not CONF.service_available.neutron):
        msg = "Skiping all Neutron cli tests because it is not available"
        raise testtools.TestCase.skipException(msg)

    def test_neutron_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.neutron,
                          'this-does-not-exist')

    def test_neutron_net_list(self):
        self.neutron('net-list')

    def test_neutron_ext_list(self):
        ext = self.parser.listing(self.neutron('ext-list'))
        self.assertTableStruct(ext, ['alias', 'name'])

    def test_neutron_dhcp_agent_list_hosting_net(self):
        self.neutron('dhcp-agent-list-hosting-net', params="private")

    def test_neutron_agent_list(self):
        agents = self.parser.listing(self.neutron('agent-list'))
        field_names = ['id', 'agent_type', 'host', 'alive', 'admin_state_up']
        self.assertTableStruct(agents, field_names)

    def test_neutron_floatingip_list(self):
        self.neutron('floatingip-list')

    def test_neutron_net_external_list(self):
        self.neutron('net-external-list')

    def test_neutron_port_list(self):
        self.neutron('port-list')

    def test_neutron_quota_list(self):
        self.neutron('quota-list')

    def test_neutron_router_list(self):
        self.neutron('router-list')

    def test_neutron_security_group_list(self):
        security_grp = self.parser.listing(self.neutron('security-group-list'))
        self.assertTableStruct(security_grp, ['id', 'name', 'description'])

    def test_neutron_security_group_rule_list(self):
        self.neutron('security-group-rule-list')

    def test_neutron_subnet_list(self):
        self.neutron('subnet-list')

    def test_neutron_help(self):
        help_text = self.neutron('help')
        lines = help_text.split('\n')
        self.assertTrue(lines[0].startswith('usage: neutron'))

        commands = []
        cmds_start = lines.index('Commands for API v2.0:')
        command_pattern = re.compile('^ {2}([a-z0-9\-\_]+)')
        for line in lines[cmds_start:]:
            match = command_pattern.match(line)
            if match:
                commands.append(match.group(1))
        commands = set(commands)
        wanted_commands = set(('net-create', 'subnet-list', 'port-delete',
                               'router-show', 'agent-update', 'help'))
        self.assertFalse(wanted_commands - commands)

     # Optional arguments:

    def test_neutron_version(self):
        self.neutron('', flags='--version')

    def test_neutron_debug_net_list(self):
        self.neutron('net-list', flags='--debug')

    def test_neutron_quiet_net_list(self):
        self.neutron('net-list', flags='--quiet')
