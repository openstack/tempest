__author__ = 'Albert'
from tempest import config
from tempest.openstack.common import log as logging
from tempest.test import attr
from tempest.test import services
from pprint import pprint
from tempest.scenario.midokura.midotools import scenario
from netaddr import IPNetwork, IPAddress

LOG = logging.getLogger(__name__)
CIDR1 = "10.10.10.8/29"

class TestMultiTenants(scenario.TestScenario):

    CONF = config.TempestConfig()

    @classmethod
    def setUpClass(cls):
        super(TestMultiTenants, cls).setUpClass()
        cls.scenario = {}

    def _scenario_conf(self):
        serverA = {
            'floating_ip': True
        }
        subnetA = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR1,
            "allocation_pools": None
        }
        networkA = {
            'subnets': [subnetA],
            'servers': [serverA],
            'tenant': 'default',
            'tenant_id': None,
            'router': True
        }
        networkB = {
            'subnets': [subnetA],
            'servers': [serverA],
            'tenant': 'extra',
            'tenant_id': None,
            'router': True
        }
        tenantA = {
            'networks': [networkA],
            'tenant_id': None,
            'type': 'default'
        }
        tenantB = {
            'networks': [networkB],
            'tenant_id': None,
            'type': 'extra'
        }
        self.scenario = {
            'tenants': [tenantA, tenantB],
        }

    def _check_floatingip(self):
        ssh_login = self.config.compute.image_ssh_user
        for server in self.servers:
            private_key = self.keypairs[server['tenant_id']].private_key
            pprint("")
            pprint(server)
            pprint("##############################")
            pprint(server.__dict__)
            #self._check_vm_connectivity(ip_address, ssh_login, private_key)

    @attr(type='smoke')
    @services('compute', 'network')
    def test_basic_multitenant_scenario(self):
        self._scenario_conf()
        self.custom_scenario(self.scenario)
        self._check_floatingip()
