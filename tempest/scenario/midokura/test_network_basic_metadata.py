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

from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario.midokura import manager
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)
SCPATH = "/network_scenarios/"


class TestNetworkBasicMetaData(manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
        TBA
    """

    def setUp(self):
        super(TestNetworkBasicMetaData, self).setUp()
        self.servers_and_keys = \
            self.setup_topology(
                '{0}scenario_basic_metadata.yaml'.format(SCPATH))

    def _check_metadata(self):
        ssh_login = CONF.compute.image_ssh_user
        try:
            for element in self.servers_and_keys:
                ip_address = element['FIP'].floating_ip_address
                private_key = element['keypair']['private_key']
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
        LOG.info("test finished, tearing down now ....")
