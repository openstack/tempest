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

from tempest_lib import exceptions

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
    def resource_setup(cls):
        if (not CONF.service_available.neutron):
            msg = "Skipping all Neutron cli tests because it is not available"
            raise cls.skipException(msg)
        super(SimpleReadOnlyNeutronClientTest, cls).resource_setup()

    def neutron(self, *args, **kwargs):
        return self.clients.neutron(*args,
                                    endpoint_type=CONF.network.endpoint_type,
                                    **kwargs)

    @test.attr(type='smoke')
    @test.idempotent_id('84dd7190-2b98-4709-8e2c-3c1d25b9e7d2')
    def test_neutron_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.neutron,
                          'this-does-not-exist')

    @test.attr(type='smoke')
    @test.idempotent_id('c598c337-313a-45ac-bf27-d6b4124a9e5b')
    def test_neutron_net_list(self):
        net_list = self.parser.listing(self.neutron('net-list'))
        self.assertTableStruct(net_list, ['id', 'name', 'subnets'])

    @test.attr(type='smoke')
    @test.idempotent_id('3e172b04-2e3b-4fcf-922d-99d5c803779f')
    def test_neutron_ext_list(self):
        ext = self.parser.listing(self.neutron('ext-list'))
        self.assertTableStruct(ext, ['alias', 'name'])

    @test.attr(type='smoke')
    @test.idempotent_id('2e0de814-52d6-4f81-be17-fe327072fc23')
    @test.requires_ext(extension='dhcp_agent_scheduler', service='network')
    def test_neutron_dhcp_agent_list_hosting_net(self):
        self.neutron('dhcp-agent-list-hosting-net',
                     params=CONF.compute.fixed_network_name)

    @test.attr(type='smoke')
    @test.idempotent_id('8524a24a-3895-40a5-8c9d-49d4459cdda4')
    @test.requires_ext(extension='agent', service='network')
    def test_neutron_agent_list(self):
        agents = self.parser.listing(self.neutron('agent-list'))
        field_names = ['id', 'agent_type', 'host', 'alive', 'admin_state_up']
        self.assertTableStruct(agents, field_names)

    @test.attr(type='smoke')
    @test.idempotent_id('97c3ef92-7303-45f1-80db-b6622f176782')
    @test.requires_ext(extension='router', service='network')
    def test_neutron_floatingip_list(self):
        self.neutron('floatingip-list')

    @test.attr(type='smoke')
    @test.idempotent_id('823e0fee-404c-49a7-8bf3-d2f0383cc649')
    @test.requires_ext(extension='metering', service='network')
    def test_neutron_meter_label_list(self):
        self.neutron('meter-label-list')

    @test.attr(type='smoke')
    @test.idempotent_id('7fb76098-01f6-417f-b9c7-e630ba3f394b')
    @test.requires_ext(extension='metering', service='network')
    def test_neutron_meter_label_rule_list(self):
        self.neutron('meter-label-rule-list')

    @test.requires_ext(extension='lbaas_agent_scheduler', service='network')
    def _test_neutron_lbaas_command(self, command):
        try:
            self.neutron(command)
        except exceptions.CommandFailed as e:
            if '404 Not Found' not in e.stderr:
                self.fail('%s: Unexpected failure.' % command)

    @test.attr(type='smoke')
    @test.idempotent_id('396d1d87-fd0c-4716-9ff0-f1baa54c6c61')
    def test_neutron_lb_healthmonitor_list(self):
        self._test_neutron_lbaas_command('lb-healthmonitor-list')

    @test.attr(type='smoke')
    @test.idempotent_id('f41fa54d-5cd8-4f2c-bb4e-13abc72dccb6')
    def test_neutron_lb_member_list(self):
        self._test_neutron_lbaas_command('lb-member-list')

    @test.attr(type='smoke')
    @test.idempotent_id('3ec04885-7573-4cce-b086-5722c0b00d85')
    def test_neutron_lb_pool_list(self):
        self._test_neutron_lbaas_command('lb-pool-list')

    @test.attr(type='smoke')
    @test.idempotent_id('1ab530e0-ec87-498f-baf2-85f6635a2ad9')
    def test_neutron_lb_vip_list(self):
        self._test_neutron_lbaas_command('lb-vip-list')

    @test.attr(type='smoke')
    @test.idempotent_id('e92f7362-4009-4b37-afee-f469105b24e7')
    @test.requires_ext(extension='external-net', service='network')
    def test_neutron_net_external_list(self):
        net_ext_list = self.parser.listing(self.neutron('net-external-list'))
        self.assertTableStruct(net_ext_list, ['id', 'name', 'subnets'])

    @test.attr(type='smoke')
    @test.idempotent_id('ed840980-7c84-4b6e-b280-f13c5848a0e9')
    def test_neutron_port_list(self):
        port_list = self.parser.listing(self.neutron('port-list'))
        self.assertTableStruct(port_list, ['id', 'name', 'mac_address',
                                           'fixed_ips'])

    @test.attr(type='smoke')
    @test.idempotent_id('dded0dfa-f2ac-4c1f-bc90-69fd06dd7132')
    @test.requires_ext(extension='quotas', service='network')
    def test_neutron_quota_list(self):
        self.neutron('quota-list')

    @test.attr(type='smoke')
    @test.idempotent_id('927fca1e-4397-42a2-ba47-d738299466de')
    @test.requires_ext(extension='router', service='network')
    def test_neutron_router_list(self):
        router_list = self.parser.listing(self.neutron('router-list'))
        self.assertTableStruct(router_list, ['id', 'name',
                                             'external_gateway_info'])

    @test.attr(type='smoke')
    @test.idempotent_id('e2e3d2d5-1aee-499d-84d9-37382dcf26ff')
    @test.requires_ext(extension='security-group', service='network')
    def test_neutron_security_group_list(self):
        security_grp = self.parser.listing(self.neutron('security-group-list'))
        self.assertTableStruct(security_grp, ['id', 'name', 'description'])

    @test.attr(type='smoke')
    @test.idempotent_id('288602c2-8b59-44cd-8c5d-1ec916a114d3')
    @test.requires_ext(extension='security-group', service='network')
    def test_neutron_security_group_rule_list(self):
        security_grp = self.parser.listing(self.neutron
                                           ('security-group-rule-list'))
        self.assertTableStruct(security_grp, ['id', 'security_group',
                                              'direction', 'protocol',
                                              'remote_ip_prefix',
                                              'remote_group'])

    @test.attr(type='smoke')
    @test.idempotent_id('2a874a08-b9c9-4f0f-82ef-8cadb15bbd5d')
    def test_neutron_subnet_list(self):
        subnet_list = self.parser.listing(self.neutron('subnet-list'))
        self.assertTableStruct(subnet_list, ['id', 'name', 'cidr',
                                             'allocation_pools'])

    @test.attr(type='smoke')
    @test.idempotent_id('048e1ec3-cf6c-4066-b262-2028e03ce825')
    @test.requires_ext(extension='vpnaas', service='network')
    def test_neutron_vpn_ikepolicy_list(self):
        ikepolicy = self.parser.listing(self.neutron('vpn-ikepolicy-list'))
        self.assertTableStruct(ikepolicy, ['id', 'name',
                                           'auth_algorithm',
                                           'encryption_algorithm',
                                           'ike_version', 'pfs'])

    @test.attr(type='smoke')
    @test.idempotent_id('bb8902b7-b2e6-49fd-b9bd-a26dd99732df')
    @test.requires_ext(extension='vpnaas', service='network')
    def test_neutron_vpn_ipsecpolicy_list(self):
        ipsecpolicy = self.parser.listing(self.neutron('vpn-ipsecpolicy-list'))
        self.assertTableStruct(ipsecpolicy, ['id', 'name',
                                             'auth_algorithm',
                                             'encryption_algorithm',
                                             'pfs'])

    @test.attr(type='smoke')
    @test.idempotent_id('c0f33f9a-0ba9-4177-bcd5-dce34b81d523')
    @test.requires_ext(extension='vpnaas', service='network')
    def test_neutron_vpn_service_list(self):
        vpn_list = self.parser.listing(self.neutron('vpn-service-list'))
        self.assertTableStruct(vpn_list, ['id', 'name',
                                          'router_id', 'status'])

    @test.attr(type='smoke')
    @test.idempotent_id('bb142f8a-e568-405f-b1b7-4cb458de7971')
    @test.requires_ext(extension='vpnaas', service='network')
    def test_neutron_ipsec_site_connection_list(self):
        ipsec_site = self.parser.listing(self.neutron
                                         ('ipsec-site-connection-list'))
        self.assertTableStruct(ipsec_site, ['id', 'name',
                                            'peer_address',
                                            'peer_cidrs',
                                            'route_mode',
                                            'auth_mode', 'status'])

    @test.attr(type='smoke')
    @test.idempotent_id('89baff14-8cb7-4ad8-9c24-b0278711170b')
    @test.requires_ext(extension='fwaas', service='network')
    def test_neutron_firewall_list(self):
        firewall_list = self.parser.listing(self.neutron
                                            ('firewall-list'))
        self.assertTableStruct(firewall_list, ['id', 'name',
                                               'firewall_policy_id'])

    @test.attr(type='smoke')
    @test.idempotent_id('996e418a-2a51-4018-9602-478ca8053e61')
    @test.requires_ext(extension='fwaas', service='network')
    def test_neutron_firewall_policy_list(self):
        firewall_policy = self.parser.listing(self.neutron
                                              ('firewall-policy-list'))
        self.assertTableStruct(firewall_policy, ['id', 'name',
                                                 'firewall_rules'])

    @test.attr(type='smoke')
    @test.idempotent_id('d4638dd6-98d4-4400-a920-26572de1a6fc')
    @test.requires_ext(extension='fwaas', service='network')
    def test_neutron_firewall_rule_list(self):
        firewall_rule = self.parser.listing(self.neutron
                                            ('firewall-rule-list'))
        self.assertTableStruct(firewall_rule, ['id', 'name',
                                               'firewall_policy_id',
                                               'summary', 'enabled'])

    @test.attr(type='smoke')
    @test.idempotent_id('1c4551e1-e3f3-4af2-8a40-c3f551e4a536')
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
    @test.idempotent_id('381e6fe3-cddc-47c9-a773-70ddb2f79a91')
    def test_neutron_version(self):
        self.neutron('', flags='--version')

    @test.attr(type='smoke')
    @test.idempotent_id('bcad0e07-da8c-4c7c-8ab6-499e5d7ab8cb')
    def test_neutron_debug_net_list(self):
        self.neutron('net-list', flags='--debug')

    @test.attr(type='smoke')
    @test.idempotent_id('3e42d78e-65e5-4e8f-8c29-ca7be8feebb4')
    def test_neutron_quiet_net_list(self):
        self.neutron('net-list', flags='--quiet')
