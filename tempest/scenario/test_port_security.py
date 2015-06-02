# Copyright 2015 Cisco Systems, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging

from tempest import config
from tempest.scenario import manager
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestPortSecurityExtension(manager.NetworkScenarioTest):
    @classmethod
    def skip_checks(cls):
        super(TestPortSecurityExtension, cls).skip_checks()
        if not CONF.network_feature_enabled.port_security:
            raise cls.skipException('Port security ML2 extension '
                                    'is not supported')

    @classmethod
    def resource_setup(cls):
        super(TestPortSecurityExtension, cls).resource_setup()

    @classmethod
    def setup_credentials(cls):
        super(TestPortSecurityExtension, cls).setup_credentials()

    def setUp(self):
        super(TestPortSecurityExtension, self).setUp()

    @test.idempotent_id('eaed2e09-7228-4e37-9286-7eeb0975ac01')
    @test.services('compute', 'network')
    def test_attach_mix_ports_to_vm(self):
        """
        Create network with IpV4 subnet
        Boot VM on this network
        Create multiple ports both with port_security_enabled=False
        and port_security_enabled=True
        Attach ports to VM

        """
        network = self._create_network(tenant_id=self.tenant_id)
        self._create_subnet(network=network)
        secure_port = self._create_port(network.id,
                                        port_security_enabled=True)
        insecure_port = self._create_port(network.id,
                                          port_security_enabled=False)
        self.assertEqual(False, insecure_port['port_security_enabled'])
        create_kwargs = {'networks': [{'uuid': network.id}]}
        server = self.create_server(create_kwargs=create_kwargs)

        self.interface_client.create_interface(server=server['id'],
                                               port_id=secure_port.id)
        self.addCleanup(self.interface_client.delete_interface, server['id'],
                        secure_port['id'])

        self.interface_client.create_interface(server=server['id'],
                                               port_id=insecure_port.id)

        self.addCleanup(self.interface_client.delete_interface, server['id'],
                        insecure_port['id'])
        port_list = self._list_ports(device_id=server['id'])
        self.assertEqual(3, len(port_list))
