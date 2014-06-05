'''
Scenario:
A launched VM should get an ip address and routing table entries from DHCP. And
it should be able to metadata service.

Pre-requisites:
1 tenant
1 network
1 VM

Steps:
1. create a network
2. launch a VM
3. verify that the VM gets IP address
4. verify that the VM gets default GW in the routing table
5. verify that the VM gets a routing entry for metadata service via dhcp agent

Expected results:
vm should get an ip address (confirm by "ip addr" command) 
VM should get a defaut gw
VM should get a route for 169.254.169.254 (on non-cirros )

'''

from tempest.api.network import common as net_common
from tempest.common import debug
from tempest.common.utils.data_utils import rand_name
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest.test import attr
from tempest.test import services

LOG = logging.getLogger(__name__)


class TestNetworkBasicVMConnectivity(manager.NetworkScenarioTest):

    CONF = config.TempestConfig()

    @classmethod
    def check_preconditions(cls):
        super(TestNetworkBasicVMConnectivity, cls).check_preconditions()
        cfg = cls.config.network
        if not (cfg.tenant_networks_reachable or cfg.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicVMConnectivity, cls).setUpClass()
        cls.check_preconditions()
        cls.keypairs = {}
        cls.security_groups = {}
        cls.network = ""
        cls.subnet  = ""
        cls.server  = ""

    def _create_networks(self): 
        self.network = self._create_network(self.tenant_id)                                                                                                                                                                                           
        self.subnet = self._create_subnet(self.network)                                                                                                                                                                                                    

    def _create_keypairs(self):
        self.keypairs[self.tenant_id] = self.create_keypair(name=rand_name('keypair-smoke-'))

    def _create_security_groups(self):
        self.security_groups[self.tenant_id] = self._create_security_group()
                                 
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
        self.server = self.create_server(name=name,create_kwargs=create_kwargs)

    def _check_networks(self):
    # Checks that we see the newly created network/subnet via
    # checking the result of list_[networks,subnets]
    # Should exist only one network
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

    def _check_serverip(self):
    # Checks that the server has the assigned IP
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        for net_name, ip_addresses in self.server.networks.iteritems():
                for ip_address in ip_addresses:
                    self._check_vm_connectivity(ip_address, ssh_login, private_key)


    @services('compute', 'network')
    def test_network_basic_ops(self):
        self._create_keypairs()
        self._create_security_groups()
        self._create_networks()
        self._check_networks()
        name = rand_name('server-smoke-%d-' % 1)
        self._create_server(name, self.network)
        self._check_serverip()
