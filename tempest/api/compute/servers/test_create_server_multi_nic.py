# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ServersTestMultiNic(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(ServersTestMultiNic, cls).skip_checks()
        if not CONF.service_available.neutron:
            raise cls.skipException('Neutron service must be available.')

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServersTestMultiNic, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersTestMultiNic, cls).setup_clients()
        cls.client = cls.servers_client
        cls.networks_client = cls.os_primary.networks_client
        cls.subnets_client = cls.os_primary.subnets_client

    def _create_net_subnet_ret_net_from_cidr(self, cidr):
        name_net = data_utils.rand_name(self.__class__.__name__)
        net = self.networks_client.create_network(name=name_net)
        self.addCleanup(self.networks_client.delete_network,
                        net['network']['id'])

        subnet = self.subnets_client.create_subnet(
            network_id=net['network']['id'],
            cidr=cidr,
            ip_version=4)
        self.addCleanup(self.subnets_client.delete_subnet,
                        subnet['subnet']['id'])
        return net

    @decorators.idempotent_id('0578d144-ed74-43f8-8e57-ab10dbf9b3c2')
    def test_verify_multiple_nics_order(self):
        # Verify that the networks order given at the server creation is
        # preserved within the server.
        net1 = self._create_net_subnet_ret_net_from_cidr('19.80.0.0/24')
        net2 = self._create_net_subnet_ret_net_from_cidr('19.86.0.0/24')

        networks = [{'uuid': net1['network']['id']},
                    {'uuid': net2['network']['id']}]

        server_multi_nics = self.create_test_server(
            networks=networks, wait_until='ACTIVE')

        # Cleanup server; this is needed in the test case because with the LIFO
        # nature of the cleanups, if we don't delete the server first, the port
        # will still be part of the subnet and we'll get a 409 from Neutron
        # when trying to delete the subnet. The tear down in the base class
        # will try to delete the server and get a 404 but it's ignored so
        # we're OK.
        self.addCleanup(self.delete_server, server_multi_nics['id'])

        addresses = (self.client.list_addresses(server_multi_nics['id'])
                     ['addresses'])

        # We can't predict the ip addresses assigned to the server on networks.
        # Sometimes the assigned addresses are ['19.80.0.2', '19.86.0.2'], at
        # other times ['19.80.0.3', '19.86.0.3']. So we check if the first
        # address is in first network, similarly second address is in second
        # network.
        addr = [addresses[net1['network']['name']][0]['addr'],
                addresses[net2['network']['name']][0]['addr']]
        networks = [netaddr.IPNetwork('19.80.0.0/24'),
                    netaddr.IPNetwork('19.86.0.0/24')]
        for address, network in zip(addr, networks):
            self.assertIn(address, network)

    @decorators.idempotent_id('1678d144-ed74-43f8-8e57-ab10dbf9b3c2')
    def test_verify_duplicate_network_nics(self):
        # Verify that server creation does not fail when more than one nic
        # is created on the same network.
        net1 = self._create_net_subnet_ret_net_from_cidr('19.80.0.0/24')
        net2 = self._create_net_subnet_ret_net_from_cidr('19.86.0.0/24')

        networks = [{'uuid': net1['network']['id']},
                    {'uuid': net2['network']['id']},
                    {'uuid': net1['network']['id']}]

        server_multi_nics = self.create_test_server(
            networks=networks, wait_until='ACTIVE')
        self.addCleanup(self.delete_server, server_multi_nics['id'])

        addresses = (self.client.list_addresses(server_multi_nics['id'])
                     ['addresses'])

        addr = [addresses[net1['network']['name']][0]['addr'],
                addresses[net2['network']['name']][0]['addr'],
                addresses[net1['network']['name']][1]['addr']]
        networks = [netaddr.IPNetwork('19.80.0.0/24'),
                    netaddr.IPNetwork('19.86.0.0/24'),
                    netaddr.IPNetwork('19.80.0.0/24')]
        for address, network in zip(addr, networks):
            self.assertIn(address, network)
