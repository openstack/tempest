# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# All Rights Reserved.
#
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

import netaddr

from tempest.api.network import base
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class NetworksTest(base.BaseNetworkTest):

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        create a network for a tenant
        list tenant's networks
        show a tenant network details
        create a subnet for a tenant
        list tenant's subnets
        show a tenant subnet details

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [network] section of etc/tempest.conf:

        tenant_network_cidr with a block of cidr's from which smaller blocks
        can be allocated for tenant networks

        tenant_network_mask_bits with the mask bits to be used to partition the
        block defined by tenant-network_cidr
    """

    @classmethod
    def setUpClass(cls):
        super(NetworksTest, cls).setUpClass()
        cls.network = cls.create_network()
        cls.name = cls.network['name']
        cls.subnet = cls.create_subnet(cls.network)
        cls.cidr = cls.subnet['cidr']

    @attr(type='gate')
    def test_create_delete_network_subnet(self):
        # Creates a network
        name = rand_name('network-')
        resp, body = self.client.create_network(name)
        self.assertEqual('201', resp['status'])
        network = body['network']
        self.assertTrue(network['id'] is not None)
        # Find a cidr that is not in use yet and create a subnet with it
        cidr = netaddr.IPNetwork(self.network_cfg.tenant_network_cidr)
        mask_bits = self.network_cfg.tenant_network_mask_bits
        for subnet_cidr in cidr.subnet(mask_bits):
            try:
                resp, body = self.client.create_subnet(network['id'],
                                                       str(subnet_cidr))
                break
            except exceptions.BadRequest as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        self.assertEqual('201', resp['status'])
        subnet = body['subnet']
        self.assertTrue(subnet['id'] is not None)
        # Deletes subnet and network
        resp, body = self.client.delete_subnet(subnet['id'])
        self.assertEqual('204', resp['status'])
        resp, body = self.client.delete_network(network['id'])
        self.assertEqual('204', resp['status'])

    @attr(type='gate')
    def test_show_network(self):
        # Verifies the details of a network
        resp, body = self.client.show_network(self.network['id'])
        self.assertEqual('200', resp['status'])
        network = body['network']
        self.assertEqual(self.network['id'], network['id'])
        self.assertEqual(self.name, network['name'])

    @attr(type='gate')
    def test_list_networks(self):
        # Verify the network exists in the list of all networks
        resp, body = self.client.list_networks()
        networks = body['networks']
        found = any(n for n in networks if n['id'] == self.network['id'])
        self.assertTrue(found)

    @attr(type='gate')
    def test_show_subnet(self):
        # Verifies the details of a subnet
        resp, body = self.client.show_subnet(self.subnet['id'])
        self.assertEqual('200', resp['status'])
        subnet = body['subnet']
        self.assertEqual(self.subnet['id'], subnet['id'])
        self.assertEqual(self.cidr, subnet['cidr'])

    @attr(type='gate')
    def test_list_subnets(self):
        # Verify the subnet exists in the list of all subnets
        resp, body = self.client.list_subnets()
        subnets = body['subnets']
        found = any(n for n in subnets if n['id'] == self.subnet['id'])
        self.assertTrue(found)
