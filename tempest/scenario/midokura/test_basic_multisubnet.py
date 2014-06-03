__author__ = 'Albert'
from tempest.api.network import common as net_common
from tempest.common import debug
from tempest.common.utils.data_utils import rand_name
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest.test import attr
from tempest.test import services
from tempest import exceptions
from pprint import pprint
from tempest.scenario.midokura.midotools import scenario

LOG = logging.getLogger(__name__)

class TestBasicMultisubnet(manager.NetworkScenarioTest):

    CONF = config.TempestConfig()

    @classmethod
    def setUpClass(cls):
        super(TestBasicMultisubnet, cls).setUpClass()
        cls.scenario = {}
        cls.scenario_builder = scenario

    def _scenario_conf(self):
        subnetA = {
            "network_id": None,
            "ip_version": 4,
            "cidr": "10.10.10.10/29",
            "allocation_pools": None
        }
        subnetB = {
            "network_id": None,
            "ip_version": 4,
            "cidr": "10.10.1.10/29",
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
        servers = self.scenario_builder.get_servers
        for server in servers:
            pprint(server.__dict__)


    @attr(type='smoke')
    @services('compute', 'network')
    def test_basic_multisubnet_scenario(self):
        self._scenario_conf()
        self.scenario.custom_scenario(self.scenario)
        self.assertTrue(self._check_vm_assignation())