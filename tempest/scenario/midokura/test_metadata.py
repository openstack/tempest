__author__ = 'Albert'
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

from tempest.api.network import common as net_common
from tempest.common import debug
from tempest.common.utils.data_utils import rand_name
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest.test import attr
from tempest.test import services
from tempest.common import ssh
from tempest import exceptions
from pprint import pprint

LOG = logging.getLogger(__name__)


class TestMetaData(manager.NetworkScenarioTest):

    CONF = config.TempestConfig()

    @classmethod
    def check_preconditions(cls):
        super(TestMetaData, cls).check_preconditions()
        cfg = cls.config.network
        if not (cfg.tenant_networks_reachable or cfg.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)


    @classmethod
    def setUpClass(cls):
        super(TestMetaData, cls).setUpClass()
        cls.check_preconditions()
        cls.keypairs = {}
        cls.security_groups = {}
        cls.networks = []
        cls.subnets = []
        cls.routers = []
        cls.servers = []
        cls.floating_ips = {}

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
            return net_common.AttributeDict(**result['router'])
        elif network_id:
            router = self._create_router(tenant_id)
            router.add_gateway(network_id)
            return router
        else:
            raise Exception("Neither of 'public_router_id' or "
                            "'public_network_id' has been defined.")

    def _create_router(self, tenant_id, namestart='router-smoke-'):
        name = rand_name(namestart)
        body = dict(
            router=dict(
                name=name,
                admin_state_up=True,
                tenant_id=tenant_id,
                ),
            )
        result = self.network_client.create_router(body=body)
        router = net_common.DeletableRouter(client=self.network_client,
                                            **result['router'])
        self.assertEqual(router.name, name)
        self.set_resource(name, router)
        return router

    def _create_keypairs(self):
        self.keypairs[self.tenant_id] = self.create_keypair(
            name=rand_name('keypair-smoke-'))

    def _create_security_groups(self):
        self.security_groups[self.tenant_id] = self._create_security_group()

    def _create_networks(self):
        network = self._create_network(self.tenant_id)
        router = self._get_router(self.tenant_id)
        subnet = self._create_subnet(network)
        subnet.add_to_router(router.id)
        self.networks.append(network)
        self.subnets.append(subnet)
        self.routers.append(router)

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
            name = rand_name('server-smoke-%d-' % i)
            server = self._create_server(name, network)
            self.servers.append(server)

    def _assign_floating_ips(self):
        public_network_id = self.config.network.public_network_id
        for server in self.servers:
            floating_ip = self._create_floating_ip(server, public_network_id)
            self.floating_ips.setdefault(server, [])
            self.floating_ips[server].append(floating_ip)

    def _scenario(self):
        self._create_keypairs()
        self._create_security_groups()
        self._create_networks()
        self._check_networks()
        self._create_servers()
        self._assign_floating_ips()
        self._check_is_reachable_via_ssh()
        #test if everything is ok

    def _check_is_reachable_via_ssh(self):
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        try:
            for server, floating_ips in self.floating_ips.iteritems():
                for floating_ip in floating_ips:
                    ip_address = floating_ip.floating_ip_address
                    self._is_reachable_via_ssh(ip_address, ssh_login, private_key, self.config.compute.ssh_timeout)
        except Exception as exc:
            #LOG.exception(exc)
            #debug.log_ip_ns()
            raise exc

    def _check_metadata(self):
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        try:
            for server, floating_ips in self.floating_ips.iteritems():
                for floating_ip in floating_ips:
                    ip_address = floating_ip.floating_ip_address
                    ssh_client = ssh.Client(ip_address, ssh_login,
                                pkey=private_key,
                                timeout=self.config.compute.ssh_timeout)
                    result = ssh_client.exec_command("curl http://169.254.169.254")
                    _expected = "1.0\n2007-01-19\n2007-03-01\n2007-08-29\n2007-10-10\n" \
                                "2007-12-15\n2008-02-01\n2008-09-01\n2009-04-04\nlatest"
                    self.assertEqual(_expected, result)
        except Exception as exc:
            raise exc


    @attr(type='smoke')
    @services('compute', 'network')
    def test_metadata(self):
        self._scenario()
        self._check_is_reachable_via_ssh()
        self._check_metadata()
