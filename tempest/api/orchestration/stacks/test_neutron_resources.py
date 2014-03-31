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


import logging

from tempest.api.orchestration import base
from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class NeutronResourcesTestJSON(base.BaseOrchestrationTest):

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(NeutronResourcesTestJSON, cls).setUpClass()
        if not CONF.orchestration.image_ref:
            raise cls.skipException("No image available to test")
        cls.client = cls.orchestration_client
        os = clients.Manager()
        if not CONF.service_available.neutron:
            raise cls.skipException("Neutron support is required")
        cls.network_client = os.network_client
        cls.stack_name = data_utils.rand_name('heat')
        template = cls.load_template('neutron_basic')
        cls.keypair_name = (CONF.orchestration.keypair_name or
                            cls._create_keypair()['name'])
        cls.external_router_id = cls._get_external_router_id()
        cls.external_network_id = CONF.network.public_network_id

        # create the stack
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            template,
            parameters={
                'KeyName': cls.keypair_name,
                'InstanceType': CONF.orchestration.instance_type,
                'ImageId': CONF.orchestration.image_ref,
                'ExternalRouterId': cls.external_router_id,
                'ExternalNetworkId': cls.external_network_id
            })
        cls.stack_id = cls.stack_identifier.split('/')[1]
        try:
            cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')
            _, resources = cls.client.list_resources(cls.stack_identifier)
        except exceptions.TimeoutException as e:
            # attempt to log the server console to help with debugging
            # the cause of the server not signalling the waitcondition
            # to heat.
            resp, body = cls.client.get_resource(cls.stack_identifier,
                                                 'Server')
            server_id = body['physical_resource_id']
            LOG.debug('Console output for %s', server_id)
            resp, output = cls.servers_client.get_console_output(
                server_id, None)
            LOG.debug(output)
            raise e

        cls.test_resources = {}
        for resource in resources:
            cls.test_resources[resource['logical_resource_id']] = resource

    @classmethod
    def _get_external_router_id(cls):
        resp, body = cls.network_client.list_ports()
        ports = body['ports']
        router_ports = filter(lambda port: port['device_owner'] ==
                              'network:router_interface', ports)
        return router_ports[0]['device_id']

    @test.attr(type='slow')
    def test_created_resources(self):
        """Verifies created neutron resources."""
        resources = [('Network', 'OS::Neutron::Net'),
                     ('Subnet', 'OS::Neutron::Subnet'),
                     ('RouterInterface', 'OS::Neutron::RouterInterface'),
                     ('Server', 'OS::Nova::Server')]
        for resource_name, resource_type in resources:
            resource = self.test_resources.get(resource_name, None)
            self.assertIsInstance(resource, dict)
            self.assertEqual(resource_name, resource['logical_resource_id'])
            self.assertEqual(resource_type, resource['resource_type'])
            self.assertEqual('CREATE_COMPLETE', resource['resource_status'])

    @test.attr(type='slow')
    def test_created_network(self):
        """Verifies created network."""
        network_id = self.test_resources.get('Network')['physical_resource_id']
        resp, body = self.network_client.show_network(network_id)
        self.assertEqual('200', resp['status'])
        network = body['network']
        self.assertIsInstance(network, dict)
        self.assertEqual(network_id, network['id'])
        self.assertEqual('NewNetwork', network['name'])

    @test.attr(type='slow')
    def test_created_subnet(self):
        """Verifies created subnet."""
        subnet_id = self.test_resources.get('Subnet')['physical_resource_id']
        resp, body = self.network_client.show_subnet(subnet_id)
        self.assertEqual('200', resp['status'])
        subnet = body['subnet']
        network_id = self.test_resources.get('Network')['physical_resource_id']
        self.assertEqual(subnet_id, subnet['id'])
        self.assertEqual(network_id, subnet['network_id'])
        self.assertEqual('NewSubnet', subnet['name'])
        self.assertEqual('8.8.8.8', subnet['dns_nameservers'][0])
        self.assertEqual('10.0.3.20', subnet['allocation_pools'][0]['start'])
        self.assertEqual('10.0.3.150', subnet['allocation_pools'][0]['end'])
        self.assertEqual(4, subnet['ip_version'])
        self.assertEqual('10.0.3.0/24', subnet['cidr'])

    @test.attr(type='slow')
    def test_created_router(self):
        """Verifies created router."""
        router_id = self.test_resources.get('Router')['physical_resource_id']
        resp, body = self.network_client.show_router(router_id)
        self.assertEqual('200', resp['status'])
        router = body['router']
        self.assertEqual('NewRouter', router['name'])
        self.assertEqual(self.external_network_id,
                         router['external_gateway_info']['network_id'])
        self.assertEqual(False,
                         router['external_gateway_info']['enable_snat'])
        self.assertEqual(False, router['admin_state_up'])

    @test.attr(type='slow')
    def test_created_router_interface(self):
        """Verifies created router interface."""
        network_id = self.test_resources.get('Network')['physical_resource_id']
        subnet_id = self.test_resources.get('Subnet')['physical_resource_id']
        resp, body = self.network_client.list_ports()
        self.assertEqual('200', resp['status'])
        ports = body['ports']
        router_ports = filter(lambda port: port['device_id'] ==
                              self.external_router_id, ports)
        created_network_ports = filter(lambda port: port['network_id'] ==
                                       network_id, router_ports)
        self.assertEqual(1, len(created_network_ports))
        router_interface = created_network_ports[0]
        fixed_ips = router_interface['fixed_ips']
        subnet_fixed_ips = filter(lambda port: port['subnet_id'] ==
                                  subnet_id, fixed_ips)
        self.assertEqual(1, len(subnet_fixed_ips))
        router_interface_ip = subnet_fixed_ips[0]['ip_address']
        self.assertEqual('10.0.3.1', router_interface_ip)

    @test.attr(type='slow')
    def test_created_server(self):
        """Verifies created sever."""
        server_id = self.test_resources.get('Server')['physical_resource_id']
        resp, server = self.servers_client.get_server(server_id)
        self.assertEqual('200', resp['status'])
        self.assertEqual(self.keypair_name, server['key_name'])
        self.assertEqual('ACTIVE', server['status'])
        network = server['addresses']['NewNetwork'][0]
        self.assertEqual(4, network['version'])
        ip_addr_prefix = network['addr'][:7]
        ip_addr_suffix = int(network['addr'].split('.')[3])
        self.assertEqual('10.0.3.', ip_addr_prefix)
        self.assertTrue(ip_addr_suffix >= 20)
        self.assertTrue(ip_addr_suffix <= 150)
