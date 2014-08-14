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

import netaddr

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
        os = clients.Manager()
        if not CONF.service_available.neutron:
            raise cls.skipException("Neutron support is required")
        cls.network_client = os.network_client
        cls.stack_name = data_utils.rand_name('heat')
        template = cls.read_template('neutron_basic')
        cls.keypair_name = (CONF.orchestration.keypair_name or
                            cls._create_keypair()['name'])
        cls.external_network_id = CONF.network.public_network_id

        tenant_cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        mask_bits = CONF.network.tenant_network_mask_bits
        cls.subnet_cidr = tenant_cidr.subnet(mask_bits).next()

        # create the stack
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            template,
            parameters={
                'KeyName': cls.keypair_name,
                'InstanceType': CONF.orchestration.instance_type,
                'ImageId': CONF.orchestration.image_ref,
                'ExternalNetworkId': cls.external_network_id,
                'timeout': CONF.orchestration.build_timeout,
                'DNSServers': CONF.network.dns_servers,
                'SubNetCidr': str(cls.subnet_cidr)
            })
        cls.stack_id = cls.stack_identifier.split('/')[1]
        try:
            cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')
            _, resources = cls.client.list_resources(cls.stack_identifier)
        except exceptions.TimeoutException as e:
            if CONF.compute_feature_enabled.console_output:
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
        self.assertEqual(sorted(CONF.network.dns_servers),
                         sorted(subnet['dns_nameservers']))
        self.assertEqual(4, subnet['ip_version'])
        self.assertEqual(str(self.subnet_cidr), subnet['cidr'])

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
        self.assertEqual(True, router['admin_state_up'])

    @test.attr(type='slow')
    def test_created_router_interface(self):
        """Verifies created router interface."""
        router_id = self.test_resources.get('Router')['physical_resource_id']
        network_id = self.test_resources.get('Network')['physical_resource_id']
        subnet_id = self.test_resources.get('Subnet')['physical_resource_id']
        resp, body = self.network_client.list_ports()
        self.assertEqual('200', resp['status'])
        ports = body['ports']
        router_ports = filter(lambda port: port['device_id'] ==
                              router_id, ports)
        created_network_ports = filter(lambda port: port['network_id'] ==
                                       network_id, router_ports)
        self.assertEqual(1, len(created_network_ports))
        router_interface = created_network_ports[0]
        fixed_ips = router_interface['fixed_ips']
        subnet_fixed_ips = filter(lambda port: port['subnet_id'] ==
                                  subnet_id, fixed_ips)
        self.assertEqual(1, len(subnet_fixed_ips))
        router_interface_ip = subnet_fixed_ips[0]['ip_address']
        self.assertEqual(str(self.subnet_cidr.iter_hosts().next()),
                         router_interface_ip)

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
        self.assertIn(netaddr.IPAddress(network['addr']), self.subnet_cidr)
