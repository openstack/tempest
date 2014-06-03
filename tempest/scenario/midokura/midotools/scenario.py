__author__ = 'Albert'
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

class TestScenario(manager.NetworkScenarioTest):

    CONF = config.TempestConfig()

    @classmethod
    def check_preconditions(cls):
        super(TestScenario, cls).check_preconditions()
        cfg = cls.config.network
        if not (cfg.tenant_networks_reachable or cfg.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)


    @classmethod
    def setUpClass(cls):
        super(TestScenario, cls).setUpClass()
        cls.check_preconditions()
        cls.keypairs = {}
        cls.security_groups = {}
        cls.networks = []
        cls.subnets = []
        cls.routers = []
        cls.servers = []
        cls.floating_ips = {}

    def basic_scenario(self):
        self._create_keypairs()
        self._create_security_groups()
        self._create_networks()
        self._check_networks()
        self._create_servers()
        self._assign_floating_ips()

    def custom_scenario(self, scenario):
        self._create_keypairs()
        self._create_security_groups()
        for network in scenario.networks:
            self._create_custom_networks()
            self._check_networks()
            for server in network.servers:
                self._create_servers()

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

    def _create_custom_network(self, mynetwork):
        network = self._create_network(self.tenant_id)
        for mysubnet in mynetwork.subnets:
            subnet = self._create_custom_subnet(network, mysubnet)
        if mynetwork.router:
            router = self._get_router(self.tenant_id)
            subnet.add_to_router(router.id)
            self.routers.append(router)
        self.networks.append(network)
        self.subnets.append(subnet)

    def _create_custom_subnet(self, network, mysubnet, namestart='subnet-smoke-'):
        """
        Create a subnet for the given network within the cidr block
        configured for tenant networks.
        """
        result = None
        body = dict(
            subnet=dict(
                ip_version=4,
                network_id=network.id,
                tenant_id=network.tenant_id,
                cidr=str(mysubnet.cidr),
            ),
        )
        try:
            result = self.network_client.create_subnet(body=body)
        except exc.NeutronClientException as e:
            is_overlapping_cidr = 'overlaps with another subnet' in str(e)
            if not is_overlapping_cidr:
                raise
        self.assertIsNotNone(result, 'Unable to allocate tenant network')
        subnet = net_common.DeletableSubnet(client=self.network_client,
                                            **result['subnet'])
        self.assertEqual(subnet.cidr, str(mysubnet.cidr))
        self.set_resource(rand_name(namestart), subnet)
        return subnet

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