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

import testtools

from tempest.api.network import common as net_common
from tempest.common import debug
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)

Floating_IP_tuple = collections.namedtuple('Floating_IP_tuple',
                                           ['floating_ip', 'server'])


class TestNetworkBasicOps(manager.NetworkScenarioTest):

    """
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
       'tenant_networks_reachable' key) if the Tempest host should
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
    def check_preconditions(cls):
        super(TestNetworkBasicOps, cls).check_preconditions()
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestNetworkBasicOps, cls).setUpClass()
        for ext in ['router', 'security-group']:
            if not test.is_extension_enabled(ext, 'network'):
                msg = "%s extension not enabled." % ext
                raise cls.skipException(msg)
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkBasicOps, self).setUp()
        self.security_group = \
            self._create_security_group_neutron(tenant_id=self.tenant_id)
        self.network, self.subnet, self.router = self._create_networks()
        self.check_networks()
        self.servers = {}
        name = data_utils.rand_name('server-smoke')
        serv_dict = self._create_server(name, self.network)
        self.servers[serv_dict['server']] = serv_dict['keypair']
        self._check_tenant_network_connectivity()

        self._create_and_associate_floating_ips()

    def check_networks(self):
        """
        Checks that we see the newly created network/subnet/router via
        checking the result of list_[networks,routers,subnets]
        """

        seen_nets = self._list_networks()
        seen_names = [n['name'] for n in seen_nets]
        seen_ids = [n['id'] for n in seen_nets]
        self.assertIn(self.network.name, seen_names)
        self.assertIn(self.network.id, seen_ids)

        seen_subnets = self._list_subnets()
        seen_net_ids = [n['network_id'] for n in seen_subnets]
        seen_subnet_ids = [n['id'] for n in seen_subnets]
        self.assertIn(self.network.id, seen_net_ids)
        self.assertIn(self.subnet.id, seen_subnet_ids)

        seen_routers = self._list_routers()
        seen_router_ids = [n['id'] for n in seen_routers]
        seen_router_names = [n['name'] for n in seen_routers]
        self.assertIn(self.router.name,
                      seen_router_names)
        self.assertIn(self.router.id,
                      seen_router_ids)

    def _create_server(self, name, network):
        keypair = self.create_keypair(name='keypair-%s' % name)
        security_groups = [self.security_group.name]
        create_kwargs = {
            'nics': [
                {'net-id': network.id},
            ],
            'key_name': keypair.name,
            'security_groups': security_groups,
        }
        server = self.create_server(name=name, create_kwargs=create_kwargs)
        return dict(server=server, keypair=keypair)

    def _check_tenant_network_connectivity(self):
        ssh_login = CONF.compute.image_ssh_user
        for server, key in self.servers.iteritems():
            # call the common method in the parent class
            super(TestNetworkBasicOps, self).\
                _check_tenant_network_connectivity(
                    server, ssh_login, key.private_key,
                    servers_for_debug=self.servers.keys())

    def _create_and_associate_floating_ips(self):
        public_network_id = CONF.network.public_network_id
        for server in self.servers.keys():
            floating_ip = self._create_floating_ip(server, public_network_id)
            self.floating_ip_tuple = Floating_IP_tuple(floating_ip, server)

    def _check_public_network_connectivity(self, should_connect=True,
                                           msg=None):
        ssh_login = CONF.compute.image_ssh_user
        floating_ip, server = self.floating_ip_tuple
        ip_address = floating_ip.floating_ip_address
        private_key = None
        if should_connect:
            private_key = self.servers[server].private_key
        # call the common method in the parent class
        super(TestNetworkBasicOps, self)._check_public_network_connectivity(
            ip_address, ssh_login, private_key, should_connect, msg,
            self.servers.keys())

    def _disassociate_floating_ips(self):
        floating_ip, server = self.floating_ip_tuple
        self._disassociate_floating_ip(floating_ip)
        self.floating_ip_tuple = Floating_IP_tuple(
            floating_ip, None)

    def _reassociate_floating_ips(self):
        floating_ip, server = self.floating_ip_tuple
        name = data_utils.rand_name('new_server-smoke-')
        # create a new server for the floating ip
        serv_dict = self._create_server(name, self.network)
        self.servers[serv_dict['server']] = serv_dict['keypair']
        self._associate_floating_ip(floating_ip, serv_dict['server'])
        self.floating_ip_tuple = Floating_IP_tuple(
            floating_ip, serv_dict['server'])

    def _create_new_network(self):
        self.new_net = self._create_network(self.tenant_id)
        self.new_subnet = self._create_subnet(
            network=self.new_net,
            gateway_ip=None)

    def _hotplug_server(self):
        old_floating_ip, server = self.floating_ip_tuple
        ip_address = old_floating_ip.floating_ip_address
        private_key = self.servers[server].private_key
        ssh_client = self.get_remote_client(ip_address,
                                            private_key=private_key)
        old_nic_list = self._get_server_nics(ssh_client)
        # get a port from a list of one item
        port_list = self._list_ports(device_id=server.id)
        self.assertEqual(1, len(port_list))
        old_port = port_list[0]
        self.compute_client.servers.interface_attach(server=server,
                                                     net_id=self.new_net.id,
                                                     port_id=None,
                                                     fixed_ip=None)
        # move server to the head of the cleanup list
        self.addCleanup(self.delete_timeout,
                        self.compute_client.servers,
                        server.id)
        self.addCleanup(self.delete_wrapper, server)

        def check_ports():
            self.new_port_list = [port for port in
                                  self._list_ports(device_id=server.id)
                                  if port != old_port]
            return len(self.new_port_list) == 1

        if not test.call_until_true(check_ports, CONF.network.build_timeout,
                                    CONF.network.build_interval):
            raise exceptions.TimeoutException("No new port attached to the "
                                              "server in time (%s sec) !"
                                              % CONF.network.build_timeout)
        new_port = net_common.DeletablePort(client=self.network_client,
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
        ssh_client.turn_nic_on(nic=new_nic)

    def _get_server_nics(self, ssh_client):
        reg = re.compile(r'(?P<num>\d+): (?P<nic_name>\w+):')
        ipatxt = ssh_client.get_ip_list()
        return reg.findall(ipatxt)

    def _check_network_internal_connectivity(self, network):
        """
        via ssh check VM internal connectivity:
        - ping internal gateway and DHCP port, implying in-tenant connectivity
        pinging both, because L3 and DHCP agents might be on different nodes
        """
        floating_ip, server = self.floating_ip_tuple
        # get internal ports' ips:
        # get all network ports in the new network
        internal_ips = (p['fixed_ips'][0]['ip_address'] for p in
                        self._list_ports(tenant_id=server.tenant_id,
                                         network_id=network.id)
                        if p['device_owner'].startswith('network'))

        self._check_server_connectivity(floating_ip, internal_ips)

    def _check_network_external_connectivity(self):
        """
        ping public network default gateway to imply external connectivity

        """
        if not CONF.network.public_network_id:
            msg = 'public network not defined.'
            LOG.info(msg)
            return

        subnet = self.network_client.list_subnets(
            network_id=CONF.network.public_network_id)['subnets']
        self.assertEqual(1, len(subnet), "Found %d subnets" % len(subnet))

        external_ips = [subnet[0]['gateway_ip']]
        self._check_server_connectivity(self.floating_ip_tuple.floating_ip,
                                        external_ips)

    def _check_server_connectivity(self, floating_ip, address_list):
        ip_address = floating_ip.floating_ip_address
        private_key = self.servers[self.floating_ip_tuple.server].private_key
        ssh_source = self._ssh_to_server(ip_address, private_key)

        for remote_ip in address_list:
            try:
                self.assertTrue(self._check_remote_connectivity(ssh_source,
                                                                remote_ip),
                                "Timed out waiting for %s to become "
                                "reachable" % remote_ip)
            except Exception:
                LOG.exception("Unable to access {dest} via ssh to "
                              "floating-ip {src}".format(dest=remote_ip,
                                                         src=floating_ip))
                debug.log_ip_ns()
                raise

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_ops(self):
        """
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


        """
        self._check_public_network_connectivity(should_connect=True)
        self._check_network_internal_connectivity(network=self.network)
        self._check_network_external_connectivity()
        self._disassociate_floating_ips()
        self._check_public_network_connectivity(should_connect=False,
                                                msg="after disassociate "
                                                    "floating ip")
        self._reassociate_floating_ips()
        self._check_public_network_connectivity(should_connect=True,
                                                msg="after re-associate "
                                                    "floating ip")

    @testtools.skipUnless(CONF.compute_feature_enabled.interface_attach,
                          'NIC hotplug not available')
    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_hotplug_nic(self):
        """
        1. create a new network, with no gateway (to prevent overwriting VM's
            gateway)
        2. connect VM to new network
        3. set static ip and bring new nic up
        4. check VM can ping new network dhcp port

        """

        self._check_public_network_connectivity(should_connect=True)
        self._create_new_network()
        self._hotplug_server()
        self._check_network_internal_connectivity(network=self.new_net)
