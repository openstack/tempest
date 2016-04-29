# Copyright 2012 OpenStack Foundation
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
import collections
import re

from oslo_log import log as logging
import testtools

from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.scenario import manager
from tempest.scenario import network_resources
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)

Floating_IP_tuple = collections.namedtuple('Floating_IP_tuple',
                                           ['floating_ip', 'server'])


class TestNetworkBasicOps(manager.NetworkScenarioTest):

    """The test suite of network basic operations

    This smoke test suite assumes that Nova has been configured to
    boot VM's with Neutron-managed networking, and attempts to
    verify network connectivity as follows:

     There are presumed to be two types of networks: tenant and
     public.  A tenant network may or may not be reachable from the
     Tempest host.  A public network is assumed to be reachable from
     the Tempest host, and it should be possible to associate a public
     ('floating') IP address with a tenant ('fixed') IP address to
     facilitate external connectivity to a potentially unroutable
     tenant IP address.

     This test suite can be configured to test network connectivity to
     a VM via a tenant network, a public network, or both.  If both
     networking types are to be evaluated, tests that need to be
     executed remotely on the VM (via ssh) will only be run against
     one of the networks (to minimize test execution time).

     Determine which types of networks to test as follows:

     * Configure tenant network checks (via the
       'project_networks_reachable' key) if the Tempest host should
       have direct connectivity to tenant networks.  This is likely to
       be the case if Tempest is running on the same host as a
       single-node devstack installation with IP namespaces disabled.

     * Configure checks for a public network if a public network has
       been configured prior to the test suite being run and if the
       Tempest host should have connectivity to that public network.
       Checking connectivity for a public network requires that a
       value be provided for 'public_network_id'.  A value can
       optionally be provided for 'public_router_id' if tenants will
       use a shared router to access a public network (as is likely to
       be the case when IP namespaces are not enabled).  If a value is
       not provided for 'public_router_id', a router will be created
       for each tenant and use the network identified by
       'public_network_id' as its gateway.

    """

    @classmethod
    def skip_checks(cls):
        super(TestNetworkBasicOps, cls).skip_checks()
        if not (CONF.network.project_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            raise cls.skipException(msg)
        for ext in ['router', 'security-group']:
            if not test.is_extension_enabled(ext, 'network'):
                msg = "%s extension not enabled." % ext
                raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestNetworkBasicOps, cls).setup_credentials()

    def setUp(self):
        super(TestNetworkBasicOps, self).setUp()
        self.keypairs = {}
        self.servers = []

    def _setup_network_and_servers(self, **kwargs):
        boot_with_port = kwargs.pop('boot_with_port', False)
        self.security_group = \
            self._create_security_group(tenant_id=self.tenant_id)
        self.network, self.subnet, self.router = self.create_networks(**kwargs)
        self.check_networks()

        self.ports = []
        self.port_id = None
        if boot_with_port:
            # create a port on the network and boot with that
            self.port_id = self._create_port(self.network['id']).id
            self.ports.append({'port': self.port_id})

        name = data_utils.rand_name('server-smoke')
        server = self._create_server(name, self.network, self.port_id)
        self._check_tenant_network_connectivity()

        floating_ip = self.create_floating_ip(server)
        self.floating_ip_tuple = Floating_IP_tuple(floating_ip, server)

    def check_networks(self):
        """Checks that we see the newly created network/subnet/router

        via checking the result of list_[networks,routers,subnets]
        """

        seen_nets = self._list_networks()
        seen_names = [n['name'] for n in seen_nets]
        seen_ids = [n['id'] for n in seen_nets]
        self.assertIn(self.network.name, seen_names)
        self.assertIn(self.network.id, seen_ids)

        if self.subnet:
            seen_subnets = self._list_subnets()
            seen_net_ids = [n['network_id'] for n in seen_subnets]
            seen_subnet_ids = [n['id'] for n in seen_subnets]
            self.assertIn(self.network.id, seen_net_ids)
            self.assertIn(self.subnet.id, seen_subnet_ids)

        if self.router:
            seen_routers = self._list_routers()
            seen_router_ids = [n['id'] for n in seen_routers]
            seen_router_names = [n['name'] for n in seen_routers]
            self.assertIn(self.router.name,
                          seen_router_names)
            self.assertIn(self.router.id,
                          seen_router_ids)

    def _create_server(self, name, network, port_id=None):
        keypair = self.create_keypair()
        self.keypairs[keypair['name']] = keypair
        security_groups = [{'name': self.security_group['name']}]
        network = {'uuid': network.id}
        if port_id is not None:
            network['port'] = port_id

        server = self.create_server(
            name=name,
            networks=[network],
            key_name=keypair['name'],
            security_groups=security_groups,
            wait_until='ACTIVE')
        self.servers.append(server)
        return server

    def _get_server_key(self, server):
        return self.keypairs[server['key_name']]['private_key']

    def _check_tenant_network_connectivity(self):
        ssh_login = CONF.validation.image_ssh_user
        for server in self.servers:
            # call the common method in the parent class
            super(TestNetworkBasicOps, self).\
                _check_tenant_network_connectivity(
                    server, ssh_login, self._get_server_key(server),
                    servers_for_debug=self.servers)

    def check_public_network_connectivity(
            self, should_connect=True, msg=None,
            should_check_floating_ip_status=True):
        """Verifies connectivty to a VM via public network and floating IP

        and verifies floating IP has resource status is correct.

        :param should_connect: bool. determines if connectivity check is
        negative or positive.
        :param msg: Failure message to add to Error message. Should describe
        the place in the test scenario where the method was called,
        to indicate the context of the failure
        :param should_check_floating_ip_status: bool. should status of
        floating_ip be checked or not
        """
        ssh_login = CONF.validation.image_ssh_user
        floating_ip, server = self.floating_ip_tuple
        ip_address = floating_ip.floating_ip_address
        private_key = None
        floatingip_status = 'DOWN'
        if should_connect:
            private_key = self._get_server_key(server)
            floatingip_status = 'ACTIVE'
        # Check FloatingIP Status before initiating a connection
        if should_check_floating_ip_status:
            self.check_floating_ip_status(floating_ip, floatingip_status)
        # call the common method in the parent class
        super(TestNetworkBasicOps, self).check_public_network_connectivity(
            ip_address, ssh_login, private_key, should_connect, msg,
            self.servers)

    def _disassociate_floating_ips(self):
        floating_ip, server = self.floating_ip_tuple
        self._disassociate_floating_ip(floating_ip)
        self.floating_ip_tuple = Floating_IP_tuple(
            floating_ip, None)

    def _reassociate_floating_ips(self):
        floating_ip, server = self.floating_ip_tuple
        name = data_utils.rand_name('new_server-smoke')
        # create a new server for the floating ip
        server = self._create_server(name, self.network)
        self._associate_floating_ip(floating_ip, server)
        self.floating_ip_tuple = Floating_IP_tuple(
            floating_ip, server)

    def _create_new_network(self, create_gateway=False):
        self.new_net = self._create_network(tenant_id=self.tenant_id)
        if create_gateway:
            self.new_subnet = self._create_subnet(
                network=self.new_net)
        else:
            self.new_subnet = self._create_subnet(
                network=self.new_net,
                gateway_ip=None)

    def _hotplug_server(self):
        old_floating_ip, server = self.floating_ip_tuple
        ip_address = old_floating_ip.floating_ip_address
        private_key = self._get_server_key(server)
        ssh_client = self.get_remote_client(
            ip_address, private_key=private_key)
        old_nic_list = self._get_server_nics(ssh_client)
        # get a port from a list of one item
        port_list = self._list_ports(device_id=server['id'])
        self.assertEqual(1, len(port_list))
        old_port = port_list[0]
        interface = self.interface_client.create_interface(
            server_id=server['id'],
            net_id=self.new_net.id)['interfaceAttachment']
        self.addCleanup(self.ports_client.wait_for_resource_deletion,
                        interface['port_id'])
        self.addCleanup(self.delete_wrapper,
                        self.interface_client.delete_interface,
                        server['id'], interface['port_id'])

        def check_ports():
            self.new_port_list = [port for port in
                                  self._list_ports(device_id=server['id'])
                                  if port['id'] != old_port['id']]
            return len(self.new_port_list) == 1

        if not test.call_until_true(check_ports, CONF.network.build_timeout,
                                    CONF.network.build_interval):
            raise exceptions.TimeoutException(
                "No new port attached to the server in time (%s sec)! "
                "Old port: %s. Number of new ports: %d" % (
                    CONF.network.build_timeout, old_port,
                    len(self.new_port_list)))
        new_port = network_resources.DeletablePort(
            ports_client=self.ports_client,
            **self.new_port_list[0])

        def check_new_nic():
            new_nic_list = self._get_server_nics(ssh_client)
            self.diff_list = [n for n in new_nic_list if n not in old_nic_list]
            return len(self.diff_list) == 1

        if not test.call_until_true(check_new_nic, CONF.network.build_timeout,
                                    CONF.network.build_interval):
            raise exceptions.TimeoutException("Interface not visible on the "
                                              "guest after %s sec"
                                              % CONF.network.build_timeout)

        num, new_nic = self.diff_list[0]
        ssh_client.assign_static_ip(nic=new_nic,
                                    addr=new_port.fixed_ips[0]['ip_address'])
        ssh_client.set_nic_state(nic=new_nic)

    def _get_server_nics(self, ssh_client):
        reg = re.compile(r'(?P<num>\d+): (?P<nic_name>\w+):')
        ipatxt = ssh_client.get_ip_list()
        return reg.findall(ipatxt)

    def _check_network_internal_connectivity(self, network,
                                             should_connect=True):
        """via ssh check VM internal connectivity:

        - ping internal gateway and DHCP port, implying in-tenant connectivity
        pinging both, because L3 and DHCP agents might be on different nodes
        """
        floating_ip, server = self.floating_ip_tuple
        # get internal ports' ips:
        # get all network ports in the new network
        internal_ips = (p['fixed_ips'][0]['ip_address'] for p in
                        self._list_ports(tenant_id=server['tenant_id'],
                                         network_id=network.id)
                        if p['device_owner'].startswith('network'))

        self._check_server_connectivity(floating_ip,
                                        internal_ips,
                                        should_connect)

    def _check_network_external_connectivity(self):
        """ping default gateway to imply external connectivity"""
        if not CONF.network.public_network_id:
            msg = 'public network not defined.'
            LOG.info(msg)
            return

        # We ping the external IP from the instance using its floating IP
        # which is always IPv4, so we must only test connectivity to
        # external IPv4 IPs if the external network is dualstack.
        v4_subnets = [s for s in self._list_subnets(
            network_id=CONF.network.public_network_id) if s['ip_version'] == 4]
        self.assertEqual(1, len(v4_subnets),
                         "Found %d IPv4 subnets" % len(v4_subnets))

        external_ips = [v4_subnets[0]['gateway_ip']]
        self._check_server_connectivity(self.floating_ip_tuple.floating_ip,
                                        external_ips)

    def _check_server_connectivity(self, floating_ip, address_list,
                                   should_connect=True):
        ip_address = floating_ip.floating_ip_address
        private_key = self._get_server_key(self.floating_ip_tuple.server)
        ssh_source = self.get_remote_client(
            ip_address, private_key=private_key)

        for remote_ip in address_list:
            if should_connect:
                msg = ("Timed out waiting for %s to become "
                       "reachable") % remote_ip
            else:
                msg = "ip address %s is reachable" % remote_ip
            try:
                self.assertTrue(self._check_remote_connectivity
                                (ssh_source, remote_ip, should_connect),
                                msg)
            except Exception:
                LOG.exception("Unable to access {dest} via ssh to "
                              "floating-ip {src}".format(dest=remote_ip,
                                                         src=floating_ip))
                raise

    @test.attr(type='smoke')
    @test.idempotent_id('f323b3ba-82f8-4db7-8ea6-6a895869ec49')
    @test.services('compute', 'network')
    def test_network_basic_ops(self):
        """Basic network operation test

        For a freshly-booted VM with an IP address ("port") on a given
            network:

        - the Tempest host can ping the IP address.  This implies, but
         does not guarantee (see the ssh check that follows), that the
         VM has been assigned the correct IP address and has
         connectivity to the Tempest host.

        - the Tempest host can perform key-based authentication to an
         ssh server hosted at the IP address.  This check guarantees
         that the IP address is associated with the target VM.

        - the Tempest host can ssh into the VM via the IP address and
         successfully execute the following:

         - ping an external IP address, implying external connectivity.

         - ping an external hostname, implying that dns is correctly
           configured.

         - ping an internal IP address, implying connectivity to another
           VM on the same network.

        - detach the floating-ip from the VM and verify that it becomes
        unreachable

        - associate detached floating ip to a new VM and verify connectivity.
        VMs are created with unique keypair so connectivity also asserts that
        floating IP is associated with the new VM instead of the old one

        Verifies that floating IP status is updated correctly after each change


        """
        self._setup_network_and_servers()
        self.check_public_network_connectivity(should_connect=True)
        self._check_network_internal_connectivity(network=self.network)
        self._check_network_external_connectivity()
        self._disassociate_floating_ips()
        self.check_public_network_connectivity(should_connect=False,
                                               msg="after disassociate "
                                                   "floating ip")
        self._reassociate_floating_ips()
        self.check_public_network_connectivity(should_connect=True,
                                               msg="after re-associate "
                                                   "floating ip")

    @test.idempotent_id('1546850e-fbaa-42f5-8b5f-03d8a6a95f15')
    @testtools.skipIf(CONF.baremetal.driver_enabled,
                      'Baremetal relies on a shared physical network.')
    @test.services('compute', 'network')
    def test_connectivity_between_vms_on_different_networks(self):
        """Test connectivity between VMs on different networks

        For a freshly-booted VM with an IP address ("port") on a given
            network:

        - the Tempest host can ping the IP address.

        - the Tempest host can ssh into the VM via the IP address and
         successfully execute the following:

         - ping an external IP address, implying external connectivity.

         - ping an external hostname, implying that dns is correctly
           configured.

         - ping an internal IP address, implying connectivity to another
           VM on the same network.

        - Create another network on the same tenant with subnet, create
        an VM on the new network.

         - Ping the new VM from previous VM failed since the new network
         was not attached to router yet.

         - Attach the new network to the router, Ping the new VM from
         previous VM succeed.

        """
        self._setup_network_and_servers()
        self.check_public_network_connectivity(should_connect=True)
        self._check_network_internal_connectivity(network=self.network)
        self._check_network_external_connectivity()
        self._create_new_network(create_gateway=True)
        name = data_utils.rand_name('server-smoke')
        self._create_server(name, self.new_net)
        self._check_network_internal_connectivity(network=self.new_net,
                                                  should_connect=False)
        self.new_subnet.add_to_router(self.router.id)
        self._check_network_internal_connectivity(network=self.new_net,
                                                  should_connect=True)

    @test.idempotent_id('c5adff73-e961-41f1-b4a9-343614f18cfa')
    @testtools.skipUnless(CONF.compute_feature_enabled.interface_attach,
                          'NIC hotplug not available')
    @testtools.skipIf(CONF.network.port_vnic_type in ['direct', 'macvtap'],
                      'NIC hotplug not supported for '
                      'vnic_type direct or macvtap')
    @test.services('compute', 'network')
    def test_hotplug_nic(self):
        """Test hotplug network interface

        1. create a new network, with no gateway (to prevent overwriting VM's
            gateway)
        2. connect VM to new network
        3. set static ip and bring new nic up
        4. check VM can ping new network dhcp port

        """
        self._setup_network_and_servers()
        self.check_public_network_connectivity(should_connect=True)
        self._create_new_network()
        self._hotplug_server()
        self._check_network_internal_connectivity(network=self.new_net)

    @test.idempotent_id('04b9fe4e-85e8-4aea-b937-ea93885ac59f')
    @testtools.skipIf(CONF.baremetal.driver_enabled,
                      'Router state cannot be altered on a shared baremetal '
                      'network')
    @test.services('compute', 'network')
    def test_update_router_admin_state(self):
        """Test to update admin state up of router

        1. Check public connectivity before updating
                admin_state_up attribute of router to False
        2. Check public connectivity after updating
                admin_state_up attribute of router to False
        3. Check public connectivity after updating
                admin_state_up attribute of router to True
        """
        self._setup_network_and_servers()
        self.check_public_network_connectivity(
            should_connect=True, msg="before updating "
            "admin_state_up of router to False")
        self._update_router_admin_state(self.router, False)
        # TODO(alokmaurya): Remove should_check_floating_ip_status=False check
        # once bug 1396310 is fixed

        self.check_public_network_connectivity(
            should_connect=False, msg="after updating "
            "admin_state_up of router to False",
            should_check_floating_ip_status=False)
        self._update_router_admin_state(self.router, True)
        self.check_public_network_connectivity(
            should_connect=True, msg="after updating "
            "admin_state_up of router to True")

    @test.idempotent_id('d8bb918e-e2df-48b2-97cd-b73c95450980')
    @testtools.skipIf(CONF.baremetal.driver_enabled,
                      'network isolation not available for baremetal nodes')
    @testtools.skipUnless(CONF.scenario.dhcp_client,
                          "DHCP client is not available.")
    @test.services('compute', 'network')
    def test_subnet_details(self):
        """Tests that subnet's extra configuration details are affecting VMs.

         This test relies on non-shared, isolated tenant networks.

         NOTE: Neutron subnets push data to servers via dhcp-agent, so any
         update in subnet requires server to actively renew its DHCP lease.

         1. Configure subnet with dns nameserver
         2. retrieve the VM's configured dns and verify it matches the one
         configured for the subnet.
         3. update subnet's dns
         4. retrieve the VM's configured dns and verify it matches the new one
         configured for the subnet.

         TODO(yfried): add host_routes

         any resolution check would be testing either:
            * l3 forwarding (tested in test_network_basic_ops)
            * Name resolution of an external DNS nameserver - out of scope for
            Tempest
        """
        # this test check only updates (no actual resolution) so using
        # arbitrary ip addresses as nameservers, instead of parsing CONF
        initial_dns_server = '1.2.3.4'
        alt_dns_server = '9.8.7.6'

        # renewal should be immediate.
        # Timeouts are suggested by salvatore-orlando in
        # https://bugs.launchpad.net/neutron/+bug/1412325/comments/3
        renew_delay = CONF.network.build_interval
        renew_timeout = CONF.network.build_timeout

        self._setup_network_and_servers(dns_nameservers=[initial_dns_server])
        self.check_public_network_connectivity(should_connect=True)

        floating_ip, server = self.floating_ip_tuple
        ip_address = floating_ip.floating_ip_address
        private_key = self._get_server_key(server)
        ssh_client = self.get_remote_client(
            ip_address, private_key=private_key)

        dns_servers = [initial_dns_server]
        servers = ssh_client.get_dns_servers()
        self.assertEqual(set(dns_servers), set(servers),
                         'Looking for servers: {trgt_serv}. '
                         'Retrieved DNS nameservers: {act_serv} '
                         'From host: {host}.'
                         .format(host=ssh_client.ssh_client.host,
                                 act_serv=servers,
                                 trgt_serv=dns_servers))

        self.subnet.update(dns_nameservers=[alt_dns_server])
        # asserts that Neutron DB has updated the nameservers
        self.assertEqual([alt_dns_server], self.subnet.dns_nameservers,
                         "Failed to update subnet's nameservers")

        def check_new_dns_server():
            # NOTE: Server needs to renew its dhcp lease in order to get new
            # definitions from subnet
            # NOTE(amuller): we are renewing the lease as part of the retry
            # because Neutron updates dnsmasq asynchronously after the
            # subnet-update API call returns.
            ssh_client.renew_lease(fixed_ip=floating_ip['fixed_ip_address'])
            if ssh_client.get_dns_servers() != [alt_dns_server]:
                LOG.debug("Failed to update DNS nameservers")
                return False
            return True

        self.assertTrue(test.call_until_true(check_new_dns_server,
                                             renew_timeout,
                                             renew_delay),
                        msg="DHCP renewal failed to fetch "
                            "new DNS nameservers")

    @test.idempotent_id('f5dfcc22-45fd-409f-954c-5bd500d7890b')
    @testtools.skipIf(CONF.baremetal.driver_enabled,
                      'admin_state of instance ports cannot be altered '
                      'for baremetal nodes')
    @testtools.skipUnless(CONF.network_feature_enabled.port_admin_state_change,
                          "Changing a port's admin state is not supported "
                          "by the test environment")
    @test.services('compute', 'network')
    def test_update_instance_port_admin_state(self):
        """Test to update admin_state_up attribute of instance port

        1. Check public connectivity before updating
                admin_state_up attribute of instance port to False
        2. Check public connectivity after updating
                admin_state_up attribute of instance port to False
        3. Check public connectivity after updating
                admin_state_up attribute of instance port to True
        """
        self._setup_network_and_servers()
        floating_ip, server = self.floating_ip_tuple
        server_id = server['id']
        port_id = self._list_ports(device_id=server_id)[0]['id']
        self.check_public_network_connectivity(
            should_connect=True, msg="before updating "
            "admin_state_up of instance port to False")
        self.ports_client.update_port(port_id, admin_state_up=False)
        self.check_public_network_connectivity(
            should_connect=False, msg="after updating "
            "admin_state_up of instance port to False",
            should_check_floating_ip_status=False)
        self.ports_client.update_port(port_id, admin_state_up=True)
        self.check_public_network_connectivity(
            should_connect=True, msg="after updating "
            "admin_state_up of instance port to True")

    @test.idempotent_id('759462e1-8535-46b0-ab3a-33aa45c55aaa')
    @test.services('compute', 'network')
    def test_preserve_preexisting_port(self):
        """Test preserve pre-existing port

        Tests that a pre-existing port provided on server boot is not deleted
        if the server is deleted.

        Nova should unbind the port from the instance on delete if the port was
        not created by Nova as part of the boot request.
        """
        # Setup the network, create a port and boot the server from that port.
        self._setup_network_and_servers(boot_with_port=True)
        _, server = self.floating_ip_tuple
        self.assertEqual(1, len(self.ports),
                         'There should only be one port created for '
                         'server %s.' % server['id'])
        port_id = self.ports[0]['port']
        self.assertIsNotNone(port_id,
                             'Server should have been created from a '
                             'pre-existing port.')
        # Assert the port is bound to the server.
        port_list = self._list_ports(device_id=server['id'],
                                     network_id=self.network['id'])
        self.assertEqual(1, len(port_list),
                         'There should only be one port created for '
                         'server %s.' % server['id'])
        self.assertEqual(port_id, port_list[0]['id'])
        # Delete the server.
        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])
        # Assert the port still exists on the network but is unbound from
        # the deleted server.
        port = self.ports_client.show_port(port_id)['port']
        self.assertEqual(self.network['id'], port['network_id'])
        self.assertEqual('', port['device_id'])
        self.assertEqual('', port['device_owner'])

    @test.requires_ext(service='network', extension='l3_agent_scheduler')
    @test.idempotent_id('2e788c46-fb3f-4ac9-8f82-0561555bea73')
    @test.services('compute', 'network')
    def test_router_rescheduling(self):
        """Tests that router can be removed from agent and add to a new agent.

        1. Verify connectivity
        2. Remove router from all l3-agents
        3. Verify connectivity is down
        4. Assign router to new l3-agent (or old one if no new agent is
         available)
        5. Verify connectivity
        """

        # TODO(yfried): refactor this test to be used for other agents (dhcp)
        # as well

        list_hosts = (self.admin_manager.routers_client.
                      list_l3_agents_hosting_router)
        schedule_router = (self.admin_manager.network_agents_client.
                           create_router_on_l3_agent)
        unschedule_router = (self.admin_manager.network_agents_client.
                             delete_router_from_l3_agent)

        agent_list_alive = set(a["id"] for a in
                               self._list_agents(agent_type="L3 agent") if
                               a["alive"] is True)
        self._setup_network_and_servers()

        # NOTE(kevinbenton): we have to use the admin credentials to check
        # for the distributed flag because self.router only has a project view.
        admin = self.admin_manager.routers_client.show_router(self.router.id)
        if admin['router'].get('distributed', False):
            msg = "Rescheduling test does not apply to distributed routers."
            raise self.skipException(msg)

        self.check_public_network_connectivity(should_connect=True)

        # remove resource from agents
        hosting_agents = set(a["id"] for a in
                             list_hosts(self.router.id)['agents'])
        no_migration = agent_list_alive == hosting_agents
        LOG.info("Router will be assigned to {mig} hosting agent".
                 format(mig="the same" if no_migration else "a new"))

        for hosting_agent in hosting_agents:
            unschedule_router(hosting_agent, self.router.id)
            self.assertNotIn(hosting_agent,
                             [a["id"] for a in
                              list_hosts(self.router.id)['agents']],
                             'unscheduling router failed')

        # verify resource is un-functional
        self.check_public_network_connectivity(
            should_connect=False,
            msg='after router unscheduling',
            should_check_floating_ip_status=False
        )

        # schedule resource to new agent
        target_agent = list(hosting_agents if no_migration else
                            agent_list_alive - hosting_agents)[0]
        schedule_router(target_agent,
                        router_id=self.router['id'])
        self.assertEqual(
            target_agent,
            list_hosts(self.router.id)['agents'][0]['id'],
            "Router failed to reschedule. Hosting agent doesn't match "
            "target agent")

        # verify resource is functional
        self.check_public_network_connectivity(
            should_connect=True,
            msg='After router rescheduling')

    @test.requires_ext(service='network', extension='port-security')
    @testtools.skipUnless(CONF.compute_feature_enabled.interface_attach,
                          'NIC hotplug not available')
    @test.idempotent_id('7c0bb1a2-d053-49a4-98f9-ca1a1d849f63')
    @test.services('compute', 'network')
    def test_port_security_macspoofing_port(self):
        """Tests port_security extension enforces mac spoofing

        Neutron security groups always apply anti-spoof rules on the VMs. This
        allows traffic to originate and terminate at the VM as expected, but
        prevents traffic to pass through the VM. Anti-spoof rules are not
        required in cases where the VM routes traffic through it.

        The test steps are :
        1. Create a new network.
        2. Connect (hotplug) the VM to a new network.
        3. Check the VM can ping the DHCP interface of this network.
        4. Spoof the mac address of the new VM interface.
        5. Check the Security Group enforces mac spoofing and blocks pings via
           spoofed interface (VM cannot ping the DHCP interface).
        6. Disable port-security of the spoofed port- set the flag to false.
        7. Retest 3rd step and check that the Security Group allows pings via
        the spoofed interface.
        """

        spoof_mac = "00:00:00:00:00:01"

        # Create server
        self._setup_network_and_servers()
        self.check_public_network_connectivity(should_connect=True)
        self._create_new_network()
        self._hotplug_server()
        fip, server = self.floating_ip_tuple
        new_ports = self._list_ports(device_id=server["id"],
                                     network_id=self.new_net["id"])
        spoof_port = new_ports[0]
        private_key = self._get_server_key(server)
        ssh_client = self.get_remote_client(fip.floating_ip_address,
                                            private_key=private_key)
        spoof_nic = ssh_client.get_nic_name_by_mac(spoof_port["mac_address"])
        dhcp_ports = self._list_ports(device_owner="network:dhcp",
                                      network_id=self.new_net["id"])
        new_net_dhcp = dhcp_ports[0]["fixed_ips"][0]["ip_address"]
        self._check_remote_connectivity(ssh_client, dest=new_net_dhcp,
                                        nic=spoof_nic, should_succeed=True)
        ssh_client.set_mac_address(spoof_nic, spoof_mac)
        new_mac = ssh_client.get_mac_address(nic=spoof_nic)
        self.assertEqual(spoof_mac, new_mac)
        self._check_remote_connectivity(ssh_client, dest=new_net_dhcp,
                                        nic=spoof_nic, should_succeed=False)
        self.ports_client.update_port(spoof_port["id"],
                                      port_security_enabled=False,
                                      security_groups=[])
        self._check_remote_connectivity(ssh_client, dest=new_net_dhcp,
                                        nic=spoof_nic, should_succeed=True)
