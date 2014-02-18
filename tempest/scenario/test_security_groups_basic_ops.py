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

from tempest import clients
from tempest.common import debug
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest.test import attr
from tempest.test import call_until_true
from tempest.test import services

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestSecurityGroupsBasicOps(manager.NetworkScenarioTest):

    """
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
            * test than revesre traffic is enabled once an appropriate rule has
            been created on source tenant

    assumptions:
        1. alt_tenant/user existed and is different from primary_tenant/user
        2. Public network is defined and reachable from the Tempest host
        3. Public router can either be:
            * defined, in which case all tenants networks can connect directly
            to it, and cross tenant check will be done on the private IP of the
            destination tenant
            or
            * not defined (empty string), in which case each tanant will have
            its own router connected to the public network
    """

    class TenantProperties():
        """
        helper class to save tenant details
            id
            credentials
            network
            subnet
            security groups
            servers
            access point
        """

        def __init__(self, tenant_id, tenant_user, tenant_pass, tenant_name):
            self.manager = clients.OfficialClientManager(
                tenant_user,
                tenant_pass,
                tenant_name
            )
            self.keypair = None
            self.tenant_id = tenant_id
            self.tenant_name = tenant_name
            self.tenant_user = tenant_user
            self.tenant_pass = tenant_pass
            self.network = None
            self.subnet = None
            self.router = None
            self.security_groups = {}
            self.servers = list()

        def set_network(self, network, subnet, router):
            self.network = network
            self.subnet = subnet
            self.router = router

        def _get_tenant_credentials(self):
            return self.tenant_user, self.tenant_pass, self.tenant_name

    @classmethod
    def check_preconditions(cls):
        super(TestSecurityGroupsBasicOps, cls).check_preconditions()
        if (cls.alt_tenant_id is None) or (cls.tenant_id is cls.alt_tenant_id):
            msg = 'No alt_tenant defined'
            cls.enabled = False
            raise cls.skipException(msg)
        if not (CONF.network.tenant_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestSecurityGroupsBasicOps, cls).setUpClass()
        alt_creds = cls.alt_credentials()
        cls.alt_tenant_id = cls.manager._get_identity_client(
            *alt_creds
        ).tenant_id
        cls.check_preconditions()
        # TODO(mnewby) Consider looking up entities as needed instead
        # of storing them as collections on the class.
        cls.networks = []
        cls.subnets = []
        cls.routers = []
        cls.floating_ips = {}
        cls.tenants = {}
        cls.primary_tenant = cls.TenantProperties(cls.tenant_id,
                                                  *cls.credentials())
        cls.alt_tenant = cls.TenantProperties(cls.alt_tenant_id,
                                              *alt_creds)
        for tenant in [cls.primary_tenant, cls.alt_tenant]:
            cls.tenants[tenant.tenant_id] = tenant
        cls.floating_ip_access = not CONF.network.public_router_id

    def cleanup_wrapper(self, resource):
        self.cleanup_resource(resource, self.__class__.__name__)

    def setUp(self):
        super(TestSecurityGroupsBasicOps, self).setUp()
        self._deploy_tenant(self.primary_tenant)
        self._verify_network_details(self.primary_tenant)
        self._verify_mac_addr(self.primary_tenant)

    def _create_tenant_keypairs(self, tenant_id):
        keypair = self.create_keypair(
            name=data_utils.rand_name('keypair-smoke-'))
        self.addCleanup(self.cleanup_wrapper, keypair)
        self.tenants[tenant_id].keypair = keypair

    def _create_tenant_security_groups(self, tenant):
        access_sg = self._create_empty_security_group(
            namestart='secgroup_access-',
            tenant_id=tenant.tenant_id
        )
        self.addCleanup(self.cleanup_wrapper, access_sg)

        # don't use default secgroup since it allows in-tenant traffic
        def_sg = self._create_empty_security_group(
            namestart='secgroup_general-',
            tenant_id=tenant.tenant_id
        )
        self.addCleanup(self.cleanup_wrapper, def_sg)
        tenant.security_groups.update(access=access_sg, default=def_sg)
        ssh_rule = dict(
            protocol='tcp',
            port_range_min=22,
            port_range_max=22,
            direction='ingress',
        )
        rule = self._create_security_group_rule(secgroup=access_sg,
                                                **ssh_rule)
        self.addCleanup(self.cleanup_wrapper, rule)

    def _verify_network_details(self, tenant):
        # Checks that we see the newly created network/subnet/router via
        # checking the result of list_[networks,routers,subnets]
        # Check that (router, subnet) couple exist in port_list
        seen_nets = self._list_networks()
        seen_names = [n['name'] for n in seen_nets]
        seen_ids = [n['id'] for n in seen_nets]

        self.assertIn(tenant.network.name, seen_names)
        self.assertIn(tenant.network.id, seen_ids)

        seen_subnets = [(n['id'], n['cidr'], n['network_id'])
                        for n in self._list_subnets()]
        mysubnet = (tenant.subnet.id, tenant.subnet.cidr, tenant.network.id)
        self.assertIn(mysubnet, seen_subnets)

        seen_routers = self._list_routers()
        seen_router_ids = [n['id'] for n in seen_routers]
        seen_router_names = [n['name'] for n in seen_routers]

        self.assertIn(tenant.router.name, seen_router_names)
        self.assertIn(tenant.router.id, seen_router_ids)

        myport = (tenant.router.id, tenant.subnet.id)
        router_ports = [(i['device_id'], i['fixed_ips'][0]['subnet_id']) for i
                        in self.network_client.list_ports()['ports']
                        if i['device_owner'] == 'network:router_interface']

        self.assertIn(myport, router_ports)

    def _create_server(self, name, tenant, security_groups=None):
        """
        creates a server and assigns to security group
        """
        self._set_compute_context(tenant)
        if security_groups is None:
            security_groups = [tenant.security_groups['default'].name]
        create_kwargs = {
            'nics': [
                {'net-id': tenant.network.id},
            ],
            'key_name': tenant.keypair.name,
            'security_groups': security_groups,
            'tenant_id': tenant.tenant_id
        }
        server = self.create_server(name=name, create_kwargs=create_kwargs)
        self.addCleanup(self.cleanup_wrapper, server)
        return server

    def _create_tenant_servers(self, tenant, num=1):
        for i in range(num):
            name = 'server-{tenant}-gen-{num}-'.format(
                   tenant=tenant.tenant_name,
                   num=i
            )
            name = data_utils.rand_name(name)
            server = self._create_server(name, tenant)
            tenant.servers.append(server)

    def _set_access_point(self, tenant):
        """
        creates a server in a secgroup with rule allowing external ssh
        in order to access tenant internal network
        workaround ip namespace
        """
        secgroups = [sg.name for sg in tenant.security_groups.values()]
        name = 'server-{tenant}-access_point-'.format(tenant=tenant.tenant_name
                                                      )
        name = data_utils.rand_name(name)
        server = self._create_server(name, tenant,
                                     security_groups=secgroups)
        tenant.access_point = server
        self._assign_floating_ips(server)

    def _assign_floating_ips(self, server):
        public_network_id = CONF.network.public_network_id
        floating_ip = self._create_floating_ip(server, public_network_id)
        self.addCleanup(self.cleanup_wrapper, floating_ip)
        self.floating_ips.setdefault(server, floating_ip)

    def _create_tenant_network(self, tenant):
        network, subnet, router = self._create_networks(tenant.tenant_id)
        for r in [network, router, subnet]:
            self.addCleanup(self.cleanup_wrapper, r)
        tenant.set_network(network, subnet, router)

    def _set_compute_context(self, tenant):
        self.compute_client = tenant.manager.compute_client
        return self.compute_client

    def _deploy_tenant(self, tenant_or_id):
        """
        creates:
            network
            subnet
            router (if public not defined)
            access security group
            access-point server
        """
        if not isinstance(tenant_or_id, self.TenantProperties):
            tenant = self.tenants[tenant_or_id]
            tenant_id = tenant_or_id
        else:
            tenant = tenant_or_id
            tenant_id = tenant.tenant_id
        self._set_compute_context(tenant)
        self._create_tenant_keypairs(tenant_id)
        self._create_tenant_network(tenant)
        self._create_tenant_security_groups(tenant)
        self._set_access_point(tenant)

    def _get_server_ip(self, server, floating=False):
        """
        returns the ip (floating/internal) of a server
        """
        if floating:
            return self.floating_ips[server].floating_ip_address
        else:
            network_name = self.tenants[server.tenant_id].network.name
            return server.networks[network_name][0]

    def _connect_to_access_point(self, tenant):
        """
        create ssh connection to tenant access point
        """
        access_point_ssh = \
            self.floating_ips[tenant.access_point].floating_ip_address
        private_key = tenant.keypair.private_key
        access_point_ssh = self._ssh_to_server(access_point_ssh,
                                               private_key=private_key)
        return access_point_ssh

    def _test_remote_connectivity(self, source, dest, should_succeed=True):
        """
        check ping server via source ssh connection

        :param source: RemoteClient: an ssh connection from which to ping
        :param dest: and IP to ping against
        :param should_succeed: boolean should ping succeed or not
        :returns: boolean -- should_succeed == ping
        :returns: ping is false if ping failed
        """
        def ping_remote():
            try:
                source.ping_host(dest)
            except exceptions.SSHExecCommandFailed as ex:
                LOG.debug(ex)
                return not should_succeed
            return should_succeed

        return call_until_true(ping_remote,
                               CONF.compute.ping_timeout,
                               1)

    def _check_connectivity(self, access_point, ip, should_succeed=True):
        if should_succeed:
            msg = "Timed out waiting for %s to become reachable" % ip
        else:
            # todo(yfried): remove this line when bug 1252620 is fixed
            return True
            msg = "%s is reachable" % ip
        try:
            self.assertTrue(self._test_remote_connectivity(access_point, ip,
                                                           should_succeed),
                            msg)
        except Exception:
            debug.log_ip_ns()
            raise

    def _test_in_tenant_block(self, tenant):
        access_point_ssh = self._connect_to_access_point(tenant)
        for server in tenant.servers:
            self._check_connectivity(access_point=access_point_ssh,
                                     ip=self._get_server_ip(server),
                                     should_succeed=False)

    def _test_in_tenant_allow(self, tenant):
        ruleset = dict(
            protocol='icmp',
            remote_group_id=tenant.security_groups['default'].id,
            direction='ingress'
        )
        rule = self._create_security_group_rule(
            secgroup=tenant.security_groups['default'],
            **ruleset
        )
        self.addCleanup(self.cleanup_wrapper, rule)
        access_point_ssh = self._connect_to_access_point(tenant)
        for server in tenant.servers:
            self._check_connectivity(access_point=access_point_ssh,
                                     ip=self._get_server_ip(server))

    def _test_cross_tenant_block(self, source_tenant, dest_tenant):
        """
        if public router isn't defined, then dest_tenant access is via
        floating-ip
        """
        access_point_ssh = self._connect_to_access_point(source_tenant)
        ip = self._get_server_ip(dest_tenant.access_point,
                                 floating=self.floating_ip_access)
        self._check_connectivity(access_point=access_point_ssh, ip=ip,
                                 should_succeed=False)

    def _test_cross_tenant_allow(self, source_tenant, dest_tenant):
        """
        check for each direction:
        creating rule for tenant incoming traffic enables only 1way traffic
        """
        ruleset = dict(
            protocol='icmp',
            direction='ingress'
        )
        rule_s2d = self._create_security_group_rule(
            secgroup=dest_tenant.security_groups['default'],
            **ruleset
        )
        self.addCleanup(self.cleanup_wrapper, rule_s2d)
        access_point_ssh = self._connect_to_access_point(source_tenant)
        ip = self._get_server_ip(dest_tenant.access_point,
                                 floating=self.floating_ip_access)
        self._check_connectivity(access_point_ssh, ip)

        # test that reverse traffic is still blocked
        self._test_cross_tenant_block(dest_tenant, source_tenant)

        # allow reverse traffic and check
        rule_d2s = self._create_security_group_rule(
            secgroup=source_tenant.security_groups['default'],
            **ruleset
        )
        self.addCleanup(self.cleanup_wrapper, rule_d2s)

        access_point_ssh_2 = self._connect_to_access_point(dest_tenant)
        ip = self._get_server_ip(source_tenant.access_point,
                                 floating=self.floating_ip_access)
        self._check_connectivity(access_point_ssh_2, ip)

    def _verify_mac_addr(self, tenant):
        """
        verify that VM (tenant's access point) has the same ip,mac as listed in
        port list
        """
        access_point_ssh = self._connect_to_access_point(tenant)
        mac_addr = access_point_ssh.get_mac_address()
        mac_addr = mac_addr.strip().lower()
        port_list = self.network_client.list_ports()['ports']
        port_detail_list = [
            (port['fixed_ips'][0]['subnet_id'],
             port['fixed_ips'][0]['ip_address'],
             port['mac_address'].lower()) for port in port_list
        ]
        server_ip = self._get_server_ip(tenant.access_point)
        subnet_id = tenant.subnet.id
        self.assertIn((subnet_id, server_ip, mac_addr), port_detail_list)

    @attr(type='smoke')
    @services('compute', 'network')
    def test_cross_tenant_traffic(self):
        try:
            # deploy new tenant
            self._deploy_tenant(self.alt_tenant)
            self._verify_network_details(self.alt_tenant)
            self._verify_mac_addr(self.alt_tenant)

            # cross tenant check
            source_tenant = self.primary_tenant
            dest_tenant = self.alt_tenant
            self._test_cross_tenant_block(source_tenant, dest_tenant)
            self._test_cross_tenant_allow(source_tenant, dest_tenant)
        except Exception:
            for tenant in self.tenants.values():
                self._log_console_output(servers=tenant.servers)
            raise

    @attr(type='smoke')
    @services('compute', 'network')
    def test_in_tenant_traffic(self):
        try:
            self._create_tenant_servers(self.primary_tenant, num=1)

            # in-tenant check
            self._test_in_tenant_block(self.primary_tenant)
            self._test_in_tenant_allow(self.primary_tenant)

        except Exception:
            for tenant in self.tenants.values():
                self._log_console_output(servers=tenant.servers)
            raise
