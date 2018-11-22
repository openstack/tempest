# Copyright 2013 Red Hat, Inc.
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
from oslo_log import log
import testtools

from tempest.common import compute
from tempest.common import utils
from tempest.common.utils import net_info
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF
LOG = log.getLogger(__name__)


class TestSecurityGroupsBasicOps(manager.NetworkScenarioTest):

    """The test suite for security groups

    This test suite assumes that Nova has been configured to
    boot VM's with Neutron-managed networking, and attempts to
    verify cross tenant connectivity as follows

    ssh:
        in order to overcome "ip namespace", each tenant has an "access point"
        VM with floating-ip open to incoming ssh connection allowing network
        commands (ping/ssh) to be executed from within the
        tenant-network-namespace
        Tempest host performs key-based authentication to the ssh server via
        floating IP address

    connectivity test is done by pinging destination server via source server
    ssh connection.
    success - ping returns
    failure - ping_timeout reached

    multi-node:
        Multi-Node mode is enabled when CONF.compute.min_compute_nodes > 1.
        Tests connectivity between servers on different compute nodes.
        When enabled, test will boot each new server to different
        compute nodes.

    setup:
        for primary tenant:
            1. create a network&subnet
            2. create a router (if public router isn't configured)
            3. connect tenant network to public network via router
            4. create an access point:
                a. a security group open to incoming ssh connection
                b. a VM with a floating ip
            5. create a general empty security group (same as "default", but
               without rules allowing in-tenant traffic)

    tests:
        1. _verify_network_details
        2. _verify_mac_addr: for each access point verify that
           (subnet, fix_ip, mac address) are as defined in the port list
        3. _test_in_tenant_block: test that in-tenant traffic is disabled
           without rules allowing it
        4. _test_in_tenant_allow: test that in-tenant traffic is enabled
           once an appropriate rule has been created
        5. _test_cross_tenant_block: test that cross-tenant traffic is disabled
           without a rule allowing it on destination tenant
        6. _test_cross_tenant_allow:
            * test that cross-tenant traffic is enabled once an appropriate
              rule has been created on destination tenant.
            * test that reverse traffic is still blocked
            * test than reverse traffic is enabled once an appropriate rule has
              been created on source tenant
        7. _test_port_update_new_security_group:
            * test that traffic is blocked with default security group
            * test that traffic is enabled after updating port with new
              security group having appropriate rule
        8. _test_multiple_security_groups: test multiple security groups can be
           associated with the vm

    assumptions:
        1. alt_tenant/user existed and is different from primary_tenant/user
        2. Public network is defined and reachable from the Tempest host
        3. Public router can either be:
            * defined, in which case all tenants networks can connect directly
              to it, and cross tenant check will be done on the private IP of
              the destination tenant

            or

            * not defined (empty string), in which case each tenant will have
              its own router connected to the public network
    """

    credentials = ['primary', 'alt', 'admin']

    class TenantProperties(object):
        """helper class to save tenant details

            id
            credentials
            network
            subnet
            security groups
            servers
            access point
        """

        def __init__(self, clients):
            # Credentials from manager are filled with both names and IDs
            self.manager = clients
            self.creds = self.manager.credentials
            self.network = None
            self.subnet = None
            self.router = None
            self.security_groups = {}
            self.servers = list()
            self.access_point = None

        def set_network(self, network, subnet, router):
            self.network = network
            self.subnet = subnet
            self.router = router

    @classmethod
    def skip_checks(cls):
        super(TestSecurityGroupsBasicOps, cls).skip_checks()
        if CONF.network.port_vnic_type in ['direct', 'macvtap']:
            msg = ('Not currently supported when using vnic_type'
                   ' direct or macvtap')
            raise cls.skipException(msg)
        if not (CONF.network.project_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            raise cls.skipException(msg)
        if not utils.is_extension_enabled('security-group', 'network'):
            msg = "security-group extension not enabled."
            raise cls.skipException(msg)
        if CONF.network.shared_physical_network:
            msg = ('Deployment uses a shared physical network, security '
                   'groups not supported')
            raise cls.skipException(msg)
        if not CONF.network_feature_enabled.floating_ips:
            raise cls.skipException("Floating ips are not available")

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestSecurityGroupsBasicOps, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(TestSecurityGroupsBasicOps, cls).resource_setup()

        cls.multi_node = CONF.compute.min_compute_nodes > 1 and \
            compute.is_scheduler_filter_enabled("DifferentHostFilter")
        if cls.multi_node:
            LOG.info("Working in Multi Node mode")
        else:
            LOG.info("Working in Single Node mode")

        cls.floating_ips = {}
        cls.tenants = {}
        cls.primary_tenant = cls.TenantProperties(cls.os_primary)
        cls.alt_tenant = cls.TenantProperties(cls.os_alt)
        for tenant in [cls.primary_tenant, cls.alt_tenant]:
            cls.tenants[tenant.creds.tenant_id] = tenant

        cls.floating_ip_access = not CONF.network.public_router_id

    def setUp(self):
        """Set up a single tenant with an accessible server.

        If multi-host is enabled, save created server uuids.
        """
        self.servers = []

        super(TestSecurityGroupsBasicOps, self).setUp()
        self._deploy_tenant(self.primary_tenant)
        self._verify_network_details(self.primary_tenant)
        self._verify_mac_addr(self.primary_tenant)

    def _create_tenant_keypairs(self, tenant):
        keypair = self.create_keypair(tenant.manager.keypairs_client)
        tenant.keypair = keypair

    def _create_tenant_security_groups(self, tenant):
        access_sg = self._create_empty_security_group(
            namestart='secgroup_access-',
            tenant_id=tenant.creds.tenant_id,
            client=tenant.manager.security_groups_client
        )

        # don't use default secgroup since it allows in-project traffic
        def_sg = self._create_empty_security_group(
            namestart='secgroup_general-',
            tenant_id=tenant.creds.tenant_id,
            client=tenant.manager.security_groups_client
        )
        tenant.security_groups.update(access=access_sg, default=def_sg)
        ssh_rule = dict(
            protocol='tcp',
            port_range_min=22,
            port_range_max=22,
            direction='ingress',
        )
        sec_group_rules_client = tenant.manager.security_group_rules_client
        self._create_security_group_rule(
            secgroup=access_sg,
            sec_group_rules_client=sec_group_rules_client,
            **ssh_rule)

    def _verify_network_details(self, tenant):
        # Checks that we see the newly created network/subnet/router via
        # checking the result of list_[networks,routers,subnets]
        # Check that (router, subnet) couple exist in port_list
        seen_nets = self.os_admin.networks_client.list_networks()
        seen_names = [n['name'] for n in seen_nets['networks']]
        seen_ids = [n['id'] for n in seen_nets['networks']]

        self.assertIn(tenant.network['name'], seen_names)
        self.assertIn(tenant.network['id'], seen_ids)

        seen_subnets = [
            (n['id'], n['cidr'], n['network_id']) for n in
            self.os_admin.subnets_client.list_subnets()['subnets']
        ]
        mysubnet = (tenant.subnet['id'], tenant.subnet['cidr'],
                    tenant.network['id'])
        self.assertIn(mysubnet, seen_subnets)

        seen_routers = self.os_admin.routers_client.list_routers()
        seen_router_ids = [n['id'] for n in seen_routers['routers']]
        seen_router_names = [n['name'] for n in seen_routers['routers']]

        self.assertIn(tenant.router['name'], seen_router_names)
        self.assertIn(tenant.router['id'], seen_router_ids)

        myport = (tenant.router['id'], tenant.subnet['id'])
        router_ports = [
            (i['device_id'], f['subnet_id'])
            for i in self.os_admin.ports_client.list_ports(
                device_id=tenant.router['id'])['ports']
            if net_info.is_router_interface_port(i)
            for f in i['fixed_ips']
        ]

        self.assertIn(myport, router_ports)

    def _create_server(self, name, tenant, security_groups, **kwargs):
        """Creates a server and assigns it to security group.

        If multi-host is enabled, Ensures servers are created on different
        compute nodes, by storing created servers' ids and uses different_host
        as scheduler_hints on creation.
        Validates servers are created as requested, using admin client.
        """
        security_groups_names = [{'name': s['name']} for s in security_groups]
        if self.multi_node:
            kwargs["scheduler_hints"] = {'different_host': self.servers}
        server = self.create_server(
            name=name,
            networks=[{'uuid': tenant.network["id"]}],
            key_name=tenant.keypair['name'],
            security_groups=security_groups_names,
            clients=tenant.manager,
            **kwargs)
        if 'security_groups' in server:
            self.assertEqual(
                sorted([s['name'] for s in security_groups]),
                sorted([s['name'] for s in server['security_groups']]))

        # Verify servers are on different compute nodes
        if self.multi_node:
            new_host = self.get_host_for_server(server["id"])
            host_list = [self.get_host_for_server(s) for s in self.servers]
            self.assertNotIn(new_host, host_list,
                             message="Failed to boot servers on different "
                                     "Compute nodes.")

            self.servers.append(server["id"])

        return server

    def _create_tenant_servers(self, tenant, num=1):
        for i in range(num):
            name = 'server-{tenant}-gen-{num}'.format(
                   tenant=tenant.creds.tenant_name,
                   num=i
            )
            name = data_utils.rand_name(name)
            server = self._create_server(name, tenant,
                                         [tenant.security_groups['default']])
            tenant.servers.append(server)

    def _set_access_point(self, tenant):
        # creates a server in a secgroup with rule allowing external ssh
        # in order to access project internal network
        # workaround ip namespace
        secgroups = tenant.security_groups.values()
        name = 'server-{tenant}-access_point'.format(
            tenant=tenant.creds.tenant_name)
        name = data_utils.rand_name(name)
        server = self._create_server(name, tenant,
                                     security_groups=secgroups)
        tenant.access_point = server
        self._assign_floating_ips(tenant, server)

    def _assign_floating_ips(self, tenant, server):
        public_network_id = CONF.network.public_network_id
        floating_ip = self.create_floating_ip(
            server, public_network_id,
            client=tenant.manager.floating_ips_client)
        self.floating_ips.setdefault(server['id'], floating_ip)

    def _create_tenant_network(self, tenant, port_security_enabled=True):
        network, subnet, router = self.create_networks(
            networks_client=tenant.manager.networks_client,
            routers_client=tenant.manager.routers_client,
            subnets_client=tenant.manager.subnets_client,
            port_security_enabled=port_security_enabled)
        tenant.set_network(network, subnet, router)

    def _deploy_tenant(self, tenant_or_id):
        """creates:

            network
            subnet
            router (if public not defined)
            access security group
            access-point server
        """
        if not isinstance(tenant_or_id, self.TenantProperties):
            tenant = self.tenants[tenant_or_id]
        else:
            tenant = tenant_or_id
        self._create_tenant_keypairs(tenant)
        self._create_tenant_network(tenant)
        self._create_tenant_security_groups(tenant)
        self._set_access_point(tenant)

    def _get_server_ip(self, server, floating=False):
        """returns the ip (floating/internal) of a server"""
        if floating:
            server_ip = self.floating_ips[server['id']]['floating_ip_address']
        else:
            server_ip = None
            network_name = self.tenants[server['tenant_id']].network['name']
            if network_name in server['addresses']:
                server_ip = server['addresses'][network_name][0]['addr']
        return server_ip

    def _connect_to_access_point(self, tenant):
        """create ssh connection to tenant access point"""
        access_point_ssh = \
            self.floating_ips[tenant.access_point['id']]['floating_ip_address']
        private_key = tenant.keypair['private_key']
        access_point_ssh = self.get_remote_client(
            access_point_ssh, private_key=private_key,
            server=tenant.access_point)
        return access_point_ssh

    def _test_in_tenant_block(self, tenant):
        access_point_ssh = self._connect_to_access_point(tenant)
        for server in tenant.servers:
            self.check_remote_connectivity(source=access_point_ssh,
                                           dest=self._get_server_ip(server),
                                           should_succeed=False)

    def _test_in_tenant_allow(self, tenant):
        ruleset = dict(
            protocol='icmp',
            remote_group_id=tenant.security_groups['default']['id'],
            direction='ingress'
        )
        self._create_security_group_rule(
            secgroup=tenant.security_groups['default'],
            security_groups_client=tenant.manager.security_groups_client,
            **ruleset
        )
        access_point_ssh = self._connect_to_access_point(tenant)
        for server in tenant.servers:
            self.check_remote_connectivity(source=access_point_ssh,
                                           dest=self._get_server_ip(server))

    def _test_cross_tenant_block(self, source_tenant, dest_tenant):
        # if public router isn't defined, then dest_tenant access is via
        # floating-ip
        access_point_ssh = self._connect_to_access_point(source_tenant)
        ip = self._get_server_ip(dest_tenant.access_point,
                                 floating=self.floating_ip_access)
        self.check_remote_connectivity(source=access_point_ssh, dest=ip,
                                       should_succeed=False)

    def _test_cross_tenant_allow(self, source_tenant, dest_tenant):
        """check for each direction:

        creating rule for tenant incoming traffic enables only 1way traffic
        """
        ruleset = dict(
            protocol='icmp',
            direction='ingress'
        )
        sec_group_rules_client = (
            dest_tenant.manager.security_group_rules_client)
        self._create_security_group_rule(
            secgroup=dest_tenant.security_groups['default'],
            sec_group_rules_client=sec_group_rules_client,
            **ruleset
        )
        access_point_ssh = self._connect_to_access_point(source_tenant)
        ip = self._get_server_ip(dest_tenant.access_point,
                                 floating=self.floating_ip_access)
        self.check_remote_connectivity(access_point_ssh, ip)

        # test that reverse traffic is still blocked
        self._test_cross_tenant_block(dest_tenant, source_tenant)

        # allow reverse traffic and check
        sec_group_rules_client = (
            source_tenant.manager.security_group_rules_client)
        self._create_security_group_rule(
            secgroup=source_tenant.security_groups['default'],
            sec_group_rules_client=sec_group_rules_client,
            **ruleset
        )

        access_point_ssh_2 = self._connect_to_access_point(dest_tenant)
        ip = self._get_server_ip(source_tenant.access_point,
                                 floating=self.floating_ip_access)
        self.check_remote_connectivity(access_point_ssh_2, ip)

    def _verify_mac_addr(self, tenant):
        """Verify that VM has the same ip, mac as listed in port"""

        access_point_ssh = self._connect_to_access_point(tenant)
        mac_addr = access_point_ssh.get_mac_address()
        mac_addr = mac_addr.strip().lower()
        # Get the fixed_ips and mac_address fields of all ports. Select
        # only those two columns to reduce the size of the response.
        port_list = self.os_admin.ports_client.list_ports(
            fields=['fixed_ips', 'mac_address'])['ports']
        port_detail_list = [
            (port['fixed_ips'][0]['subnet_id'],
             port['fixed_ips'][0]['ip_address'],
             port['mac_address'].lower())
            for port in port_list if port['fixed_ips']
        ]
        server_ip = self._get_server_ip(tenant.access_point)
        subnet_id = tenant.subnet['id']
        self.assertIn((subnet_id, server_ip, mac_addr), port_detail_list)

    def _log_console_output_for_all_tenants(self):
        for tenant in self.tenants.values():
            client = tenant.manager.servers_client
            self._log_console_output(servers=tenant.servers, client=client)
            if tenant.access_point is not None:
                self._log_console_output(
                    servers=[tenant.access_point], client=client)

    @decorators.idempotent_id('e79f879e-debb-440c-a7e4-efeda05b6848')
    @utils.services('compute', 'network')
    def test_cross_tenant_traffic(self):
        if not self.credentials_provider.is_multi_tenant():
            raise self.skipException("No secondary tenant defined")
        try:
            # deploy new project
            self._deploy_tenant(self.alt_tenant)
            self._verify_network_details(self.alt_tenant)
            self._verify_mac_addr(self.alt_tenant)

            # cross tenant check
            source_tenant = self.primary_tenant
            dest_tenant = self.alt_tenant
            self._test_cross_tenant_block(source_tenant, dest_tenant)
            self._test_cross_tenant_allow(source_tenant, dest_tenant)
        except Exception:
            self._log_console_output_for_all_tenants()
            raise

    @decorators.idempotent_id('63163892-bbf6-4249-aa12-d5ea1f8f421b')
    @utils.services('compute', 'network')
    def test_in_tenant_traffic(self):
        try:
            self._create_tenant_servers(self.primary_tenant, num=1)

            # in-tenant check
            self._test_in_tenant_block(self.primary_tenant)
            self._test_in_tenant_allow(self.primary_tenant)
        except Exception:
            self._log_console_output_for_all_tenants()
            raise

    @decorators.idempotent_id('f4d556d7-1526-42ad-bafb-6bebf48568f6')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_port_update_new_security_group(self):
        """Verifies the traffic after updating the vm port

        With new security group having appropriate rule.
        """
        new_tenant = self.primary_tenant

        # Create empty security group and add icmp rule in it
        new_sg = self._create_empty_security_group(
            namestart='secgroup_new-',
            tenant_id=new_tenant.creds.tenant_id,
            client=new_tenant.manager.security_groups_client)
        icmp_rule = dict(
            protocol='icmp',
            direction='ingress',
        )
        sec_group_rules_client = new_tenant.manager.security_group_rules_client
        self._create_security_group_rule(
            secgroup=new_sg,
            sec_group_rules_client=sec_group_rules_client,
            **icmp_rule)
        new_tenant.security_groups.update(new_sg=new_sg)

        # Create server with default security group
        name = 'server-{tenant}-gen-1'.format(
               tenant=new_tenant.creds.tenant_name
        )
        name = data_utils.rand_name(name)
        server = self._create_server(name, new_tenant,
                                     [new_tenant.security_groups['default']])

        # Check connectivity failure with default security group
        try:
            access_point_ssh = self._connect_to_access_point(new_tenant)
            self.check_remote_connectivity(source=access_point_ssh,
                                           dest=self._get_server_ip(server),
                                           should_succeed=False)
            server_id = server['id']
            port_id = self.os_admin.ports_client.list_ports(
                device_id=server_id)['ports'][0]['id']

            # update port with new security group and check connectivity
            self.ports_client.update_port(port_id, security_groups=[
                new_tenant.security_groups['new_sg']['id']])
            self.check_remote_connectivity(
                source=access_point_ssh,
                dest=self._get_server_ip(server))
        except Exception:
            self._log_console_output_for_all_tenants()
            raise

    @decorators.idempotent_id('d2f77418-fcc4-439d-b935-72eca704e293')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_multiple_security_groups(self):
        """Verify multiple security groups and checks that rules

        provided in the both the groups is applied onto VM
        """
        tenant = self.primary_tenant
        ip = self._get_server_ip(tenant.access_point,
                                 floating=self.floating_ip_access)
        ssh_login = CONF.validation.image_ssh_user
        private_key = tenant.keypair['private_key']
        self.check_vm_connectivity(ip,
                                   should_connect=False)
        ruleset = dict(
            protocol='icmp',
            direction='ingress'
        )
        self._create_security_group_rule(
            secgroup=tenant.security_groups['default'],
            **ruleset
        )
        # NOTE: Vm now has 2 security groups one with ssh rule(
        # already added in setUp() method),and other with icmp rule
        # (added in the above step).The check_vm_connectivity tests
        # -that vm ping test is successful
        # -ssh to vm is successful
        self.check_vm_connectivity(ip,
                                   username=ssh_login,
                                   private_key=private_key,
                                   should_connect=True)

    @decorators.attr(type='slow')
    @utils.requires_ext(service='network', extension='port-security')
    @decorators.idempotent_id('7c811dcc-263b-49a3-92d2-1b4d8405f50c')
    @utils.services('compute', 'network')
    def test_port_security_disable_security_group(self):
        """Verify the default security group rules is disabled."""
        new_tenant = self.primary_tenant

        # Create server
        name = 'server-{tenant}-gen-1'.format(
               tenant=new_tenant.creds.tenant_name
        )
        name = data_utils.rand_name(name)
        server = self._create_server(name, new_tenant,
                                     [new_tenant.security_groups['default']])

        access_point_ssh = self._connect_to_access_point(new_tenant)
        server_id = server['id']
        port_id = self.os_admin.ports_client.list_ports(
            device_id=server_id)['ports'][0]['id']

        # Flip the port's port security and check connectivity
        try:
            self.ports_client.update_port(port_id,
                                          port_security_enabled=True,
                                          security_groups=[])
            self.check_remote_connectivity(source=access_point_ssh,
                                           dest=self._get_server_ip(server),
                                           should_succeed=False)

            self.ports_client.update_port(port_id,
                                          port_security_enabled=False,
                                          security_groups=[])
            self.check_remote_connectivity(
                source=access_point_ssh,
                dest=self._get_server_ip(server))
        except Exception:
            self._log_console_output_for_all_tenants()
            raise

    @decorators.attr(type='slow')
    @utils.requires_ext(service='network', extension='port-security')
    @decorators.idempotent_id('13ccf253-e5ad-424b-9c4a-97b88a026699')
    # TODO(mriedem): We shouldn't actually need to check this since neutron
    # disables the port_security extension by default, but the problem is nova
    # assumes port_security_enabled=True if it's not set on the network
    # resource, which will mean nova may attempt to apply a security group on
    # a port on that network which would fail. This is really a bug in nova.
    @testtools.skipUnless(
        CONF.network_feature_enabled.port_security,
        'Port security must be enabled.')
    @utils.services('compute', 'network')
    def test_boot_into_disabled_port_security_network_without_secgroup(self):
        tenant = self.primary_tenant
        self._create_tenant_network(tenant, port_security_enabled=False)
        self.assertFalse(tenant.network['port_security_enabled'])
        name = data_utils.rand_name('server-smoke')
        sec_groups = []
        server = self._create_server(name, tenant, sec_groups)
        server_id = server['id']
        ports = self.os_admin.ports_client.list_ports(
            device_id=server_id)['ports']
        self.assertEqual(1, len(ports))
        for port in ports:
            self.assertEmpty(port['security_groups'],
                             "Neutron shouldn't even use it's default sec "
                             "group.")
