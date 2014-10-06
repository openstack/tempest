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

import os

from tempest.openstack.common import log as logging
from tempest.scenario.midokura import manager
from tempest import test


LOG = logging.getLogger(__name__)
SCPATH = "/network_scenarios/"


class TestNetworkAdvancedMetadata(manager.AdvancedNetworkScenarioTest):
    """
    Description:
        VMs on a neutron network, which is NOT connected to a router,
         should be able to get metadata service through dhcp agent
    Prerequisites:
        1. launched VM should have a route for MD service
        via DHCP agent's IP address. This route entry is
        injected by DHCP, but cirros OS doesn't support
        setting routes via DHCP (option 121).
        For cirros, add the entry manually as follows
        $ ip route add 169.254.169.254 via 10.0.0.2
        where 10.0.0.2 is the ip address of DHCP agent
        (change it accordingly)
    Steps:
        1. inside VM type:
            curl http://169.254.169.254
    Expected result:
        should forward the MD traffic to DHCP
        agent so the VM can retrieve metadata.
        1. In a VM, curl
        http://169.254.169.254/2009-04-04/meta-data/instance-id
        should return its instance id
    """

    @classmethod
    def setUpClass(cls):
        super(TestNetworkAdvancedMetadata, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkAdvancedMetadata, self).setUp()
        self.servers_and_keys = \
            self.setup_topology(os.path.abspath(
                '{0}scenario_advanced_metadata.yaml'.format(SCPATH)))

    def _check_metadata(self):
        try:
            ap_details = self.servers_and_keys[-1]
            hops = [(ap_details['FIP'].floating_ip_address,
                     ap_details['keypair']['private_key'])]
            server = self.servers_and_keys[0]['server']
            name = server['addresses'].keys()[0]
            remote_ip = server['addresses'][name][0]['addr']
            pk = self.servers_and_keys[0]['keypair']['private_key']
            hops.append((remote_ip, pk))
            ssh_client = self.setup_tunnel(hops)
            result = \
                ssh_client.exec_command("curl http://169.254.169.254")
            LOG.info(result)
            expected = \
                "1.0\n2007-01-19\n2007-03-01\n2007-08-29\n2007-10-10\n" \
                "2007-12-15\n2008-02-01\n2008-09-01\n2009-04-04\nlatest"
            self.assertEqual(expected, result)
        except Exception as exc:
            raise exc

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_advanced_metadata(self):
        self._check_metadata()
        LOG.info("test finished, tearing down now ....")
