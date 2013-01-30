# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import logging
import subprocess

import netaddr

from quantumclient.common import exceptions as exc

from tempest.common.utils.data_utils import rand_name
from tempest import smoke
from tempest import test


LOG = logging.getLogger(__name__)


class AttributeDict(dict):

    """
    Provide attribute access (dict.key) to dictionary values.
    """

    def __getattr__(self, name):
        """Allow attribute access for all keys in the dict."""
        if name in self:
            return self[name]
        return super(AttributeDict, self).__getattribute__(name)


class DeletableResource(AttributeDict):

    """
    Support deletion of quantum resources (networks, subnets) via a
    delete() method, as is supported by keystone and nova resources.
    """

    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        super(DeletableResource, self).__init__(*args, **kwargs)

    def __str__(self):
        return '<%s id="%s" name="%s">' % (self.__class__.__name__,
                                           self.id, self.name)

    def delete(self):
        raise NotImplemented()


class DeletableNetwork(DeletableResource):

    def delete(self):
        self.client.delete_network(self.id)


class DeletableSubnet(DeletableResource):

    _router_ids = set()

    def add_to_router(self, router_id):
        self._router_ids.add(router_id)
        body = dict(subnet_id=self.id)
        self.client.add_interface_router(router_id, body=body)

    def delete(self):
        for router_id in self._router_ids.copy():
            body = dict(subnet_id=self.id)
            self.client.remove_interface_router(router_id, body=body)
            self._router_ids.remove(router_id)
        self.client.delete_subnet(self.id)


class DeletableRouter(DeletableResource):

    def add_gateway(self, network_id):
        body = dict(network_id=network_id)
        self.client.add_gateway_router(self.id, body=body)

    def delete(self):
        self.client.remove_gateway_router(self.id)
        self.client.delete_router(self.id)


class DeletableFloatingIp(DeletableResource):

    def delete(self):
        self.client.delete_floatingip(self.id)


class TestNetworkBasicOps(smoke.DefaultClientSmokeTest):

    """
    This smoke test suite assumes that Nova has been configured to
    boot VM's with Quantum-managed networking, and attempts to
    verify network connectivity as follows:

     * For a freshly-booted VM with an IP address ("port") on a given network:

       - the Tempest host can ping the IP address.  This implies that
         the VM has been assigned the correct IP address and has
         connectivity to the Tempest host.

       #TODO(mnewby) - Need to implement the following:
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
     faciliate external connectivity to a potentially unroutable
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
        cfg = cls.config.network
        msg = None
        if not (cfg.tenant_networks_reachable or cfg.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
        else:
            try:
                cls.network_client.list_networks()
            except exc.QuantumClientException:
                msg = 'Unable to connect to Quantum service.'

        cls.enabled = not bool(msg)
        if msg:
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicOps, cls).setUpClass()
        cls.check_preconditions()
        cfg = cls.config.network
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.username,
            cls.config.identity.password,
            cls.config.identity.tenant_name).tenant_id
        # TODO(mnewby) Consider looking up entities as needed instead
        # of storing them as collections on the class.
        cls.keypairs = {}
        cls.security_groups = {}
        cls.networks = []
        cls.subnets = []
        cls.routers = []
        cls.servers = []
        cls.floating_ips = {}

    def _create_keypair(self, client):
        kp_name = rand_name('keypair-smoke-')
        keypair = client.keypairs.create(kp_name)
        try:
            self.assertEqual(keypair.id, kp_name)
            self.set_resource(kp_name, keypair)
        except AttributeError:
            self.fail("Keypair object not successfully created.")
        return keypair

    def _create_security_group(self, client):
        # Create security group
        sg_name = rand_name('secgroup-smoke-')
        sg_desc = sg_name + " description"
        secgroup = client.security_groups.create(sg_name, sg_desc)
        try:
            self.assertEqual(secgroup.name, sg_name)
            self.assertEqual(secgroup.description, sg_desc)
            self.set_resource(sg_name, secgroup)
        except AttributeError:
            self.fail("SecurityGroup object not successfully created.")

        # Add rules to the security group
        rulesets = [
            {
                # ssh
                'ip_protocol': 'tcp',
                'from_port': 22,
                'to_port': 22,
                'cidr': '0.0.0.0/0',
                'group_id': secgroup.id
            },
            {
                # ping
                'ip_protocol': 'icmp',
                'from_port': -1,
                'to_port': -1,
                'cidr': '0.0.0.0/0',
                'group_id': secgroup.id
            }
        ]
        for ruleset in rulesets:
            try:
                client.security_group_rules.create(secgroup.id, **ruleset)
            except Exception:
                self.fail("Failed to create rule in security group.")

        return secgroup

    def _get_router(self, tenant_id):
        """Retrieve a router for the given tenant id.

        If a public router has been configured, it will be returned.

        If a public router has not been configured, but a public
        network has, a tenant router will be created and returned that
        routes traffic to the public network.

        """
        router_id = self.config.network.public_router_id
        network_id = self.config.network.public_network_id
        if router_id:
            result = self.network_client.show_router(router_id)
            return AttributeDict(**result['router'])
        elif network_id:
            router = self._create_router(tenant_id)
            router.add_gateway(network_id)
            return router
        else:
            raise Exception("Neither of 'public_router_id' or "
                            "'public_network_id' has been defined.")

    def _create_router(self, tenant_id):
        name = rand_name('router-smoke-')
        body = dict(
            router=dict(
                name=name,
                admin_state_up=True,
                tenant_id=tenant_id,
            ),
        )
        result = self.network_client.create_router(body=body)
        router = DeletableRouter(client=self.network_client,
                                 **result['router'])
        self.assertEqual(router.name, name)
        self.set_resource(name, router)
        return router

    def _create_network(self, tenant_id):
        name = rand_name('network-smoke-')
        body = dict(
            network=dict(
                name=name,
                tenant_id=tenant_id,
            ),
        )
        result = self.network_client.create_network(body=body)
        network = DeletableNetwork(client=self.network_client,
                                   **result['network'])
        self.assertEqual(network.name, name)
        self.set_resource(name, network)
        return network

    def _list_networks(self):
        nets = self.network_client.list_networks()
        return nets['networks']

    def _list_subnets(self):
        subnets = self.network_client.list_subnets()
        return subnets['subnets']

    def _list_routers(self):
        routers = self.network_client.list_routers()
        return routers['routers']

    def _create_subnet(self, network):
        """
        Create a subnet for the given network within the cidr block
        configured for tenant networks.
        """
        cfg = self.config.network
        tenant_cidr = netaddr.IPNetwork(cfg.tenant_network_cidr)
        result = None
        # Repeatedly attempt subnet creation with sequential cidr
        # blocks until an unallocated block is found.
        for subnet_cidr in tenant_cidr.subnet(cfg.tenant_network_mask_bits):
            body = dict(
                subnet=dict(
                ip_version=4,
                network_id=network.id,
                tenant_id=network.tenant_id,
                cidr=str(subnet_cidr),
                ),
            )
            try:
                result = self.network_client.create_subnet(body=body)
                break
            except exc.QuantumClientException as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        self.assertIsNotNone(result, 'Unable to allocate tenant network')
        subnet = DeletableSubnet(client=self.network_client,
                                 **result['subnet'])
        self.assertEqual(subnet.cidr, str(subnet_cidr))
        self.set_resource(rand_name('subnet-smoke-'), subnet)
        return subnet

    def _create_server(self, client, network, name, key_name, security_groups):
        flavor_id = self.config.compute.flavor_ref
        base_image_id = self.config.compute.image_ref
        create_kwargs = {
            'nics': [
                {'net-id': network.id},
            ],
            'key_name': key_name,
            'security_groups': security_groups,
        }
        server = client.servers.create(name, base_image_id, flavor_id,
                                       **create_kwargs)
        try:
            self.assertEqual(server.name, name)
            self.set_resource(name, server)
        except AttributeError:
            self.fail("Server not successfully created.")
        self.status_timeout(client.servers, server.id, 'ACTIVE')
        # The instance retrieved on creation is missing network
        # details, necessitating retrieval after it becomes active to
        # ensure correct details.
        server = client.servers.get(server.id)
        self.set_resource(name, server)
        return server

    def _create_floating_ip(self, server, external_network_id):
        result = self.network_client.list_ports(device_id=server.id)
        ports = result.get('ports', [])
        self.assertEqual(len(ports), 1,
                         "Unable to determine which port to target.")
        port_id = ports[0]['id']
        body = dict(
            floatingip=dict(
                floating_network_id=external_network_id,
                port_id=port_id,
                tenant_id=server.tenant_id,
            )
        )
        result = self.network_client.create_floatingip(body=body)
        floating_ip = DeletableFloatingIp(client=self.network_client,
                                          **result['floatingip'])
        self.set_resource(rand_name('floatingip-'), floating_ip)
        return floating_ip

    def _ping_ip_address(self, ip_address):
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.wait()
            if proc.returncode == 0:
                return True

        # TODO(mnewby) Allow configuration of execution and sleep duration.
        return test.call_until_true(ping, 20, 1)

    def test_001_create_keypairs(self):
        self.keypairs[self.tenant_id] = self._create_keypair(
            self.compute_client)

    def test_002_create_security_groups(self):
        self.security_groups[self.tenant_id] = self._create_security_group(
            self.compute_client)

    def test_003_create_networks(self):
        network = self._create_network(self.tenant_id)
        router = self._get_router(self.tenant_id)
        subnet = self._create_subnet(network)
        subnet.add_to_router(router.id)
        self.networks.append(network)
        self.subnets.append(subnet)
        self.routers.append(router)

    def test_004_check_networks(self):
        #Checks that we see the newly created network/subnet/router via
        #checking the result of list_[networks,routers,subnets]
        seen_nets = self._list_networks()
        seen_names = [n['name'] for n in seen_nets]
        seen_ids = [n['id'] for n in seen_nets]
        for mynet in self.networks:
            assert mynet.name in seen_names, \
            "Did not see expected network with name %s" % mynet.name
            assert mynet.id in seen_ids, \
            "Did not see expected network with id %s" % mynet.id
        seen_subnets = self._list_subnets()
        seen_net_ids = [n['network_id'] for n in seen_subnets]
        seen_subnet_ids = [n['id'] for n in seen_subnets]
        for mynet in self.networks:
            assert mynet.id in seen_net_ids, \
            "Did not see subnet belonging to network %s/%s" % \
            (mynet.name, mynet.id)
        for mysubnet in self.subnets:
            assert mysubnet.id in seen_subnet_ids, \
            "Did not see expected subnet with id %s" % \
            mysubnet.id
        seen_routers = self._list_routers()
        seen_router_ids = [n['id'] for n in seen_routers]
        seen_router_names = [n['name'] for n in seen_routers]
        for myrouter in self.routers:
            assert myrouter.name in seen_router_names, \
            "Did not see expected router with name %s" % \
            myrouter.name
            assert myrouter.id in seen_router_ids, \
            "Did not see expected router with id %s" % \
            myrouter.id

    def test_005_create_servers(self):
        if not (self.keypairs or self.security_groups or self.networks):
            raise self.skipTest('Necessary resources have not been defined')
        for i, network in enumerate(self.networks):
            tenant_id = network.tenant_id
            name = rand_name('server-smoke-%d-' % i)
            keypair_name = self.keypairs[tenant_id].name
            security_groups = [self.security_groups[tenant_id].name]
            server = self._create_server(self.compute_client, network,
                                         name, keypair_name, security_groups)
            self.servers.append(server)

    def test_006_check_tenant_network_connectivity(self):
        if not self.config.network.tenant_networks_reachable:
            msg = 'Tenant networks not configured to be reachable.'
            raise self.skipTest(msg)
        if not self.servers:
            raise self.skipTest("No VM's have been created")
        for server in self.servers:
            for net_name, ip_addresses in server.networks.iteritems():
                for ip_address in ip_addresses:
                    self.assertTrue(self._ping_ip_address(ip_address),
                                    "Timed out waiting for %s's ip to become "
                                    "reachable" % server.name)

    def test_007_assign_floating_ips(self):
        public_network_id = self.config.network.public_network_id
        if not public_network_id:
            raise self.skipTest('Public network not configured')
        if not self.servers:
            raise self.skipTest("No VM's have been created")
        for server in self.servers:
            floating_ip = self._create_floating_ip(server, public_network_id)
            self.floating_ips.setdefault(server, [])
            self.floating_ips[server].append(floating_ip)

    def test_008_check_public_network_connectivity(self):
        if not self.floating_ips:
            raise self.skipTest('No floating ips have been allocated.')
        for server, floating_ips in self.floating_ips.iteritems():
            for floating_ip in floating_ips:
                ip_address = floating_ip.floating_ip_address
                self.assertTrue(self._ping_ip_address(ip_address),
                                "Timed out waiting for %s's ip to become "
                                "reachable" % server.name)
