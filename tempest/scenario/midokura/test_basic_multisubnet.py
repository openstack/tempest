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
CIDR2 = "10.10.1.8/29"

class TestBasicMultisubnet(scenario.TestScenario):

    CONF = config.TempestConfig()

    @classmethod
    def setUpClass(cls):
        super(TestBasicMultisubnet, cls).setUpClass()
        cls.scenario = {}

    def _scenario_conf(self):
        subnetA = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR1,
            "allocation_pools": None
        }
        subnetB = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR2,
            "allocation_pools": None
        }
        networkA = {
            'subnets': [subnetA, subnetB],
            'servers': ['serverA', 'serverB', 'serverC', 'serverD', 'serverE']
        }
        self.scenario = {
            'networks': [networkA],
        }

    def _check_vm_assignation(self):
        s1 = 0
        s2 = 0
        for server in self.servers:
            network = server.addresses
            key, value = network.popitem()
            ip = value[0]['addr']
            pprint(ip)
            if IPAddress(ip) in IPNetwork(CIDR1):
                s1 += 1
            else:
                s2 += 1
        return s1 == 4 or s2 == 4

    @attr(type='smoke')
    @services('compute', 'network')
    def test_basic_multisubnet_scenario(self):
        self._scenario_conf()
        self.custom_scenario(self.scenario)
        self.assertTrue(self._check_vm_assignation())