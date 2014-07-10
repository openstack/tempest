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

from tempest import cli
from tempest import config
from tempest.openstack.common import log as logging
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyNeutronClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Neutron CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def setUpClass(cls):
        if (not CONF.service_available.neutron):
            msg = "Skipping all Neutron cli tests because it is not available"
            raise cls.skipException(msg)
        super(SimpleReadOnlyNeutronClientTest, cls).setUpClass()

    @test.attr(type='smoke')
    def test_neutron_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.neutron,
                          'this-does-not-exist')

    @test.attr(type='smoke')
    def test_neutron_net_list(self):
        net_list = self.parser.listing(self.neutron('net-list'))
        self.assertTableStruct(net_list, ['id', 'name', 'subnets'])

    @test.attr(type='smoke')
    def test_neutron_ext_list(self):
        ext = self.parser.listing(self.neutron('ext-list'))
        self.assertTableStruct(ext, ['alias', 'name'])

    @test.attr(type='smoke')
    @test.requires_ext(extension='dhcp_agent_scheduler', service='network')
    def test_neutron_dhcp_agent_list_hosting_net(self):
        self.neutron('dhcp-agent-list-hosting-net',
                     params=CONF.compute.fixed_network_name)

    @test.attr(type='smoke')
    @test.requires_ext(extension='agent', service='network')
    def test_neutron_agent_list(self):
        agents = self.parser.listing(self.neutron('agent-list'))
        field_names = ['id', 'agent_type', 'host', 'alive', 'admin_state_up']
        self.assertTableStruct(agents, field_names)

    @test.attr(type='smoke')
    @test.requires_ext(extension='router', service='network')
    def test_neutron_floatingip_list(self):
        self.neutron('floatingip-list')

    @test.attr(type='smoke')
    @test.requires_ext(extension='metering', service='network')
    def test_neutron_meter_label_list(self):
        self.neutron('meter-label-list')

    @test.attr(type='smoke')
    @test.requires_ext(extension='metering', service='network')
    def test_neutron_meter_label_rule_list(self):
        self.neutron('meter-label-rule-list')

    @test.requires_ext(extension='lbaas_agent_scheduler', service='network')
    def _test_neutron_lbaas_command(self, command):
        try:
            self.neutron(command)
        except cli.CommandFailed as e:
            if '404 Not Found' not in e.stderr:
                self.fail('%s: Unexpected failure.' % command)

    @test.attr(type='smoke')
    def test_neutron_lb_healthmonitor_list(self):
        self._test_neutron_lbaas_command('lb-healthmonitor-list')

    @test.attr(type='smoke')
    def test_neutron_lb_member_list(self):
        self._test_neutron_lbaas_command('lb-member-list')

    @test.attr(type='smoke')
    def test_neutron_lb_pool_list(self):
        self._test_neutron_lbaas_command('lb-pool-list')

    @test.attr(type='smoke')
    def test_neutron_lb_vip_list(self):
        self._test_neutron_lbaas_command('lb-vip-list')

    @test.attr(type='smoke')
    @test.requires_ext(extension='external-net', service='network')
    def test_neutron_net_external_list(self):
        net_ext_list = self.parser.listing(self.neutron('net-external-list'))
        self.assertTableStruct(net_ext_list, ['id', 'name', 'subnets'])

    @test.attr(type='smoke')
    def test_neutron_port_list(self):
        port_list = self.parser.listing(self.neutron('port-list'))
        self.assertTableStruct(port_list, ['id', 'name', 'mac_address',
                                           'fixed_ips'])

    @test.attr(type='smoke')
    @test.requires_ext(extension='quotas', service='network')
    def test_neutron_quota_list(self):
        self.neutron('quota-list')

    @test.attr(type='smoke')
    @test.requires_ext(extension='router', service='network')
    def test_neutron_router_list(self):
        router_list = self.parser.listing(self.neutron('router-list'))
        self.assertTableStruct(router_list, ['id', 'name',
                                             'external_gateway_info'])

    @test.attr(type='smoke')
    @test.requires_ext(extension='security-group', service='network')
    def test_neutron_security_group_list(self):
        security_grp = self.parser.listing(self.neutron('security-group-list'))
        self.assertTableStruct(security_grp, ['id', 'name', 'description'])

    @test.attr(type='smoke')
    @test.requires_ext(extension='security-group', service='network')
    def test_neutron_security_group_rule_list(self):
        security_grp = self.parser.listing(self.neutron
                                           ('security-group-rule-list'))
        self.assertTableStruct(security_grp, ['id', 'security_group',
                                              'direction', 'protocol',
                                              'remote_ip_prefix',
                                              'remote_group'])

    @test.attr(type='smoke')
    def test_neutron_subnet_list(self):
        subnet_list = self.parser.listing(self.neutron('subnet-list'))
        self.assertTableStruct(subnet_list, ['id', 'name', 'cidr',
                                             'allocation_pools'])

    @test.attr(type='smoke')
    def test_neutron_help(self):
        help_text = self.neutron('help')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'usage: neutron')

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

    @test.attr(type='smoke')
    def test_neutron_version(self):
        self.neutron('', flags='--version')

    @test.attr(type='smoke')
    def test_neutron_debug_net_list(self):
        self.neutron('net-list', flags='--debug')

    @test.attr(type='smoke')
    def test_neutron_quiet_net_list(self):
        self.neutron('net-list', flags='--quiet')
