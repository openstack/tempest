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

from tempest.common import debug
from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestNetworkBasicOps(manager.NetworkScenarioTest):

    """
    This smoke test suite assumes that Nova has been configured to
    boot VM's with Neutron-managed networking, and attempts to
    verify network connectivity as follows:

     * For a freshly-booted VM with an IP address ("port") on a given network:

       - the Tempest host can ping the IP address.  This implies, but
         does not guarantee (see the ssh check that follows), that the
         VM has been assigned the correct IP address and has
         connectivity to the Tempest host.

       - the Tempest host can perform key-based authentication to an
         ssh server hosted at the IP address.  This check guarantees
         that the IP address is associated with the target VM.

       - detach the floating-ip from the VM and verify that it becomes
       unreachable

       - associate detached floating ip to a new VM and verify connectivity.
       VMs are created with unique keypair so connectivity also asserts that
       floating IP is associated with the new VM instead of the old one

       # TODO(mnewby) - Need to implement the following:
       - the Tempest host can ssh into the VM via the IP address and
         successfully execute the following:

         - ping an external IP address, implying external connectivity.

         - ping an external hostname, implying that dns is correctly
           configured.

         - ping an internal IP address, implying connectivity to another
           VM on the same network.

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
        super(TestNetworkBasicOps, cls).setUpClass()
        for ext in ['router', 'security-group']:
            if not test.is_extension_enabled(ext, 'network'):
                msg = "%s extension not enabled." % ext
                raise cls.skipException(msg)
        cls.check_preconditions()

    def cleanup_wrapper(self, resource):
        self.cleanup_resource(resource, self.__class__.__name__)

    def setUp(self):
        super(TestNetworkBasicOps, self).setUp()
        self.security_group = \
            self._create_security_group_neutron(tenant_id=self.tenant_id)
        self.addCleanup(self.cleanup_wrapper, self.security_group)
        self.network, self.subnet, self.router = self._create_networks()
        for r in [self.network, self.router, self.subnet]:
            self.addCleanup(self.cleanup_wrapper, r)
        self.check_networks()
        self.servers = {}
        name = data_utils.rand_name('server-smoke')
        serv_dict = self._create_server(name, self.network)
        self.servers[serv_dict['server']] = serv_dict['keypair']
        self._check_tenant_network_connectivity()
        self.floating_ips = {}
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
        self.addCleanup(self.cleanup_wrapper, keypair)
        security_groups = [self.security_group.name]
        create_kwargs = {
            'nics': [
                {'net-id': network.id},
            ],
            'key_name': keypair.name,
            'security_groups': security_groups,
        }
        server = self.create_server(name=name, create_kwargs=create_kwargs)
        self.addCleanup(self.cleanup_wrapper, server)
        return dict(server=server, keypair=keypair)

    def _create_servers(self):
        for i, network in enumerate(self.networks):
            name = data_utils.rand_name('server-smoke-%d-' % i)
            self._create_server(name, network)

    def _check_tenant_network_connectivity(self):
        if not CONF.network.tenant_networks_reachable:
            msg = 'Tenant networks not configured to be reachable.'
            LOG.info(msg)
            return
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        ssh_login = CONF.compute.image_ssh_user
        try:
            for server, key in self.servers.iteritems():
                for net_name, ip_addresses in server.networks.iteritems():
                    for ip_address in ip_addresses:
                        self._check_vm_connectivity(ip_address, ssh_login,
                                                    key.private_key)
        except Exception:
            LOG.exception('Tenant connectivity check failed')
            self._log_console_output(servers=self.servers.keys())
            debug.log_ip_ns()
            raise

    def _create_and_associate_floating_ips(self):
        public_network_id = CONF.network.public_network_id
        for server in self.servers.keys():
            floating_ip = self._create_floating_ip(server, public_network_id)
            self.floating_ips[floating_ip] = server
            self.addCleanup(self.cleanup_wrapper, floating_ip)

    def _check_public_network_connectivity(self, should_connect=True,
                                           msg=None):
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        ssh_login = CONF.compute.image_ssh_user
        LOG.debug('checking network connections')
        try:
            for floating_ip, server in self.floating_ips.iteritems():
                ip_address = floating_ip.floating_ip_address
                private_key = None
                if should_connect:
                    private_key = self.servers[server].private_key
                self._check_vm_connectivity(ip_address,
                                            ssh_login,
                                            private_key,
                                            should_connect=should_connect)
        except Exception:
            ex_msg = 'Public network connectivity check failed'
            if msg:
                ex_msg += ": " + msg
            LOG.exception(ex_msg)
            self._log_console_output(servers=self.servers.keys())
            debug.log_ip_ns()
            raise

    def _disassociate_floating_ips(self):
        for floating_ip, server in self.floating_ips.iteritems():
            self._disassociate_floating_ip(floating_ip)
            self.floating_ips[floating_ip] = None

    def _reassociate_floating_ips(self):
        for floating_ip in self.floating_ips.keys():
            name = data_utils.rand_name('new_server-smoke-')
            # create a new server for the floating ip
            serv_dict = self._create_server(name, self.network)
            self.servers[serv_dict['server']] = serv_dict['keypair']
            self._associate_floating_ip(floating_ip, serv_dict['server'])
            self.floating_ips[floating_ip] = serv_dict['server']

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_ops(self):
        self._check_public_network_connectivity(should_connect=True)
        self._disassociate_floating_ips()
        self._check_public_network_connectivity(should_connect=False,
                                                msg="after disassociate "
                                                    "floating ip")
        self._reassociate_floating_ips()
        self._check_public_network_connectivity(should_connect=True,
                                                msg="after re-associate "
                                                    "floating ip")
