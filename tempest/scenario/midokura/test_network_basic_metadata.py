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
__author__ = 'Albert'
__email__ = "albert.vico@midokura.com"

from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import scenario
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)
CIDR1 = "10.10.1.0/24"


class TestMetaData(scenario.TestScenario):

    @classmethod
    def setUpClass(cls):
        super(TestMetaData, cls).setUpClass()
        cls.scenario = {}

    def setUp(self):
        super(TestMetaData, self).setUp()
        self.security_group = \
            self._create_security_group_neutron(
                tenant_id=self.tenant_id)
        self._scenario_conf()
        self.custom_scenario(self.scenario)

    def _scenario_conf(self):
        serverA = {
            'floating_ip': True,
            'sg': None,
        }
        routerA = {
            "public": True,
            "name": "router_1"
        }
        subnetA = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR1,
            "allocation_pools": None,
            "routers": [routerA],
            "dns": [],
            "routes": [],
        }
        networkA = {
            'subnets': [subnetA],
            'servers': [serverA],
        }
        tenantA = {
            'networks': [networkA],
            'tenant_id': None,
            'type': 'default',
            'hasgateway': False,
            'MasterKey': False,
        }
        self.scenario = {
            'tenants': [tenantA],
        }

    def _check_metadata(self):
        ssh_login = CONF.compute.image_ssh_user
        try:
            floating_ip, server = self.floating_ip_tuple
            ip_address = floating_ip.floating_ip_address
            private_key = self.servers[server].private_key
            linux_client = \
                self.get_remote_client(ip_address, ssh_login, private_key)
            result = \
                linux_client.exec_command("curl http://169.254.169.254")
            LOG.info(result)
            _expected = \
                "1.0\n2007-01-19\n2007-03-01\n2007-08-29\n2007-10-10\n" \
                "2007-12-15\n2008-02-01\n2008-09-01\n2009-04-04\nlatest"
            self.assertEqual(_expected, result)
        except Exception as exc:
            raise exc

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_metadata(self):
        self._check_metadata()
