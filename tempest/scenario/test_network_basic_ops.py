# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.openstack.common import jsonutils
from tempest.openstack.common import log as logging
from tempest.scenario import manager

import tempest.test
from tempest.test import attr
from tempest.test import services

LOG = logging.getLogger(__name__)


class FloatingIPCheckTracker(object):
    """
    Checking VM connectivity through floating IP addresses is bound to fail
    if the floating IP has not actually been associated with the VM yet.
    This helper class facilitates checking for floating IP assignments on
    VMs. It only checks for a given IP address once.
    """

    def __init__(self, compute_client, floating_ip_map):
        self.compute_client = compute_client
        self.unchecked = floating_ip_map.copy()

    def run_checks(self):
        """Check for any remaining unverified floating IPs

        Gets VM details from nova and checks for floating IPs
        within the returned information. Returns true when all
        checks are complete and is suitable for use with
        tempest.test.call_until_true()
        """
        to_delete = []
        loggable_map = {}
        for check_addr, server in self.unchecked.iteritems():
            serverdata = self.compute_client.servers.get(server.id)
            ip_addr = [addr for sublist in serverdata.networks.values() for
                       addr in sublist]
            if check_addr.floating_ip_address in ip_addr:
                to_delete.append(check_addr)
            else:
                loggable_map[server.id] = check_addr

        for to_del in to_delete:
            del self.unchecked[to_del]

        LOG.debug('Unchecked floating IPs: %s',
                  jsonutils.dumps(loggable_map))
        return len(self.unchecked) == 0


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

    CONF = config.TempestConfig()

    @classmethod
    def check_preconditions(cls):
        super(TestNetworkBasicOps, cls).check_preconditions()
        cfg = cls.config.network
        if not (cfg.tenant_networks_reachable or cfg.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicOps, cls).setUpClass()
        cls.check_preconditions()
        # TODO(mnewby) Consider looking up entities as needed instead
        # of storing them as collections on the class.
        cls.keypairs = {}
        cls.security_groups = {}
        cls.networks = []
        cls.subnets = []
        cls.routers = []
        cls.servers = []
        cls.floating_ips = {}

    def _create_keypairs(self):
        self.keypairs[self.tenant_id] = self.create_keypair(
            name=data_utils.rand_name('keypair-smoke-'))

    def _create_security_groups(self):
        self.security_groups[self.tenant_id] =\
            self._create_security_group_neutron(tenant_id=self.tenant_id)

    def _check_networks(self):
        # Checks that we see the newly created network/subnet/router via
        # checking the result of list_[networks,routers,subnets]
        seen_nets = self._list_networks()
        seen_names = [n['name'] for n in seen_nets]
        seen_ids = [n['id'] for n in seen_nets]
        for mynet in self.networks:
            self.assertIn(mynet.name, seen_names)
            self.assertIn(mynet.id, seen_ids)
        seen_subnets = self._list_subnets()
        seen_net_ids = [n['network_id'] for n in seen_subnets]
        seen_subnet_ids = [n['id'] for n in seen_subnets]
        for mynet in self.networks:
            self.assertIn(mynet.id, seen_net_ids)
        for mysubnet in self.subnets:
            self.assertIn(mysubnet.id, seen_subnet_ids)
        seen_routers = self._list_routers()
        seen_router_ids = [n['id'] for n in seen_routers]
        seen_router_names = [n['name'] for n in seen_routers]
        for myrouter in self.routers:
            self.assertIn(myrouter.name, seen_router_names)
            self.assertIn(myrouter.id, seen_router_ids)

    def _create_server(self, name, network):
        tenant_id = network.tenant_id
        keypair_name = self.keypairs[tenant_id].name
        security_groups = [self.security_groups[tenant_id].name]
        create_kwargs = {
            'nics': [
                {'net-id': network.id},
            ],
            'key_name': keypair_name,
            'security_groups': security_groups,
        }
        server = self.create_server(name=name, create_kwargs=create_kwargs)
        return server

    def _create_servers(self):
        for i, network in enumerate(self.networks):
            name = data_utils.rand_name('server-smoke-%d-' % i)
            server = self._create_server(name, network)
            self.servers.append(server)

    def _check_tenant_network_connectivity(self):
        if not self.config.network.tenant_networks_reachable:
            msg = 'Tenant networks not configured to be reachable.'
            LOG.info(msg)
            return
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        try:
            for server in self.servers:
                for net_name, ip_addresses in server.networks.iteritems():
                    for ip_address in ip_addresses:
                        self._check_vm_connectivity(ip_address, ssh_login,
                                                    private_key)
        except Exception as exc:
            LOG.exception(exc)
            debug.log_ip_ns()
            raise exc

    def _wait_for_floating_ip_association(self):
        ip_tracker = FloatingIPCheckTracker(self.compute_client,
                                            self.floating_ips)

        self.assertTrue(
            tempest.test.call_until_true(
                ip_tracker.run_checks, self.config.compute.build_timeout,
                self.config.compute.build_interval),
            "Timed out while waiting for the floating IP assignments "
            "to propagate")

    def _create_and_associate_floating_ips(self):
        public_network_id = self.config.network.public_network_id
        for server in self.servers:
            floating_ip = self._create_floating_ip(server, public_network_id)
            self.floating_ips[floating_ip] = server

    def _check_public_network_connectivity(self, should_connect=True):
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        try:
            for floating_ip, server in self.floating_ips.iteritems():
                ip_address = floating_ip.floating_ip_address
                self._check_vm_connectivity(ip_address,
                                            ssh_login,
                                            private_key,
                                            should_connect=should_connect)
        except Exception as exc:
            LOG.exception(exc)
            debug.log_ip_ns()
            raise exc

    def _disassociate_floating_ips(self):
        for floating_ip, server in self.floating_ips.iteritems():
            self._disassociate_floating_ip(floating_ip)
            self.floating_ips[floating_ip] = None

    @attr(type='smoke')
    @services('compute', 'network')
    def test_network_basic_ops(self):
        self._create_keypairs()
        self._create_security_groups()
        self._create_networks()
        self._check_networks()
        self._create_servers()
        self._create_and_associate_floating_ips()
        self._wait_for_floating_ip_association()
        self._check_tenant_network_connectivity()
        self._check_public_network_connectivity(should_connect=True)
        self._disassociate_floating_ips()
        self._check_public_network_connectivity(should_connect=False)
