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
from tempest.test import attr


LOG = logging.getLogger(__name__)


class NeutronResourcesTestJSON(base.BaseOrchestrationTest):
    _interface = 'json'

    template = """
HeatTemplateFormatVersion: '2012-12-12'
Description: |
  Template which creates single EC2 instance
Parameters:
  KeyName:
    Type: String
  InstanceType:
    Type: String
  ImageId:
    Type: String
  ExternalRouterId:
    Type: String
Resources:
  Network:
    Type: OS::Quantum::Net
    Properties: {name: NewNetwork}
  Subnet:
    Type: OS::Quantum::Subnet
    Properties:
      network_id: {Ref: Network}
      name: NewSubnet
      ip_version: 4
      cidr: 10.0.3.0/24
      dns_nameservers: ["8.8.8.8"]
      allocation_pools:
      - {end: 10.0.3.150, start: 10.0.3.20}
  RouterInterface:
    Type: OS::Quantum::RouterInterface
    Properties:
      router_id: {Ref: ExternalRouterId}
      subnet_id: {Ref: Subnet}
  Server:
    Type: AWS::EC2::Instance
    Metadata:
      Name: SmokeServer
    Properties:
      ImageId: {Ref: ImageId}
      InstanceType: {Ref: InstanceType}
      KeyName: {Ref: KeyName}
      SubnetId: {Ref: Subnet}
      UserData:
        Fn::Base64:
          Fn::Join:
          - ''
          - - '#!/bin/bash -v

              '
            - /opt/aws/bin/cfn-signal -e 0 -r "SmokeServer created" '
            - {Ref: WaitHandle}
            - '''

              '
  WaitHandle:
    Type: AWS::CloudFormation::WaitConditionHandle
  WaitCondition:
    Type: AWS::CloudFormation::WaitCondition
    DependsOn: Server
    Properties:
      Handle: {Ref: WaitHandle}
      Timeout: '600'
"""

    @classmethod
    def setUpClass(cls):
        super(NeutronResourcesTestJSON, cls).setUpClass()
        if not cls.orchestration_cfg.image_ref:
            raise cls.skipException("No image available to test")
        cls.client = cls.orchestration_client
        os = clients.Manager()
        cls.network_cfg = os.config.network
        if not cls.config.service_available.neutron:
            raise cls.skipException("Neutron support is required")
        cls.network_client = os.network_client
        cls.stack_name = data_utils.rand_name('heat')
        cls.keypair_name = (cls.orchestration_cfg.keypair_name or
                            cls._create_keypair()['name'])
        cls.external_router_id = cls._get_external_router_id()

        # create the stack
        cls.stack_identifier = cls.create_stack(
            cls.stack_name,
            cls.template,
            parameters={
                'KeyName': cls.keypair_name,
                'InstanceType': cls.orchestration_cfg.instance_type,
                'ImageId': cls.orchestration_cfg.image_ref,
                'ExternalRouterId': cls.external_router_id
            })
        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.client.wait_for_stack_status(cls.stack_id, 'CREATE_COMPLETE')
        _, resources = cls.client.list_resources(cls.stack_identifier)
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

    @attr(type='slow')
    def test_created_resources(self):
        """Verifies created neutron resources."""
        resources = [('Network', 'OS::Quantum::Net'),
                     ('Subnet', 'OS::Quantum::Subnet'),
                     ('RouterInterface', 'OS::Quantum::RouterInterface'),
                     ('Server', 'AWS::EC2::Instance')]
        for resource_name, resource_type in resources:
            resource = self.test_resources.get(resource_name, None)
            self.assertIsInstance(resource, dict)
            self.assertEqual(resource_name, resource['logical_resource_id'])
            self.assertEqual(resource_type, resource['resource_type'])
            self.assertEqual('CREATE_COMPLETE', resource['resource_status'])

    @attr(type='slow')
    def test_created_network(self):
        """Verifies created network."""
        network_id = self.test_resources.get('Network')['physical_resource_id']
        resp, body = self.network_client.show_network(network_id)
        self.assertEqual('200', resp['status'])
        network = body['network']
        self.assertIsInstance(network, dict)
        self.assertEqual(network_id, network['id'])
        self.assertEqual('NewNetwork', network['name'])

    @attr(type='slow')
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

    @attr(type='slow')
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

    @attr(type='slow')
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
