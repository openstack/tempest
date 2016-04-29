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
import testtools

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest import test

CONF = config.CONF


class ServersTestJSON(base.BaseV2ComputeTest):
    disk_config = 'AUTO'

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServersTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client
        cls.networks_client = cls.os.networks_client
        cls.subnets_client = cls.os.subnets_client

    @classmethod
    def resource_setup(cls):
        cls.set_validation_resources()
        super(ServersTestJSON, cls).resource_setup()
        cls.meta = {'hello': 'world'}
        cls.accessIPv4 = '1.1.1.1'
        cls.accessIPv6 = '0000:0000:0000:0000:0000:babe:220.12.22.2'
        cls.name = data_utils.rand_name('server')
        cls.password = data_utils.rand_password()
        disk_config = cls.disk_config
        cls.server_initial = cls.create_test_server(
            validatable=True,
            wait_until='ACTIVE',
            name=cls.name,
            metadata=cls.meta,
            accessIPv4=cls.accessIPv4,
            accessIPv6=cls.accessIPv6,
            disk_config=disk_config,
            adminPass=cls.password)
        cls.server = (cls.client.show_server(cls.server_initial['id'])
                      ['server'])

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

    @test.attr(type='smoke')
    @test.idempotent_id('5de47127-9977-400a-936f-abcfbec1218f')
    def test_verify_server_details(self):
        # Verify the specified server attributes are set correctly
        self.assertEqual(self.accessIPv4, self.server['accessIPv4'])
        # NOTE(maurosr): See http://tools.ietf.org/html/rfc5952 (section 4)
        # Here we compare directly with the canonicalized format.
        self.assertEqual(self.server['accessIPv6'],
                         str(netaddr.IPAddress(self.accessIPv6)))
        self.assertEqual(self.name, self.server['name'])
        self.assertEqual(self.image_ref, self.server['image']['id'])
        self.assertEqual(self.flavor_ref, self.server['flavor']['id'])
        self.assertEqual(self.meta, self.server['metadata'])

    @test.attr(type='smoke')
    @test.idempotent_id('9a438d88-10c6-4bcd-8b5b-5b6e25e1346f')
    def test_list_servers(self):
        # The created server should be in the list of all servers
        body = self.client.list_servers()
        servers = body['servers']
        found = any([i for i in servers if i['id'] == self.server['id']])
        self.assertTrue(found)

    @test.idempotent_id('585e934c-448e-43c4-acbf-d06a9b899997')
    def test_list_servers_with_detail(self):
        # The created server should be in the detailed list of all servers
        body = self.client.list_servers(detail=True)
        servers = body['servers']
        found = any([i for i in servers if i['id'] == self.server['id']])
        self.assertTrue(found)

    @test.idempotent_id('cbc0f52f-05aa-492b-bdc1-84b575ca294b')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_verify_created_server_vcpus(self):
        # Verify that the number of vcpus reported by the instance matches
        # the amount stated by the flavor
        flavor = self.flavors_client.show_flavor(self.flavor_ref)['flavor']
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server),
            self.ssh_user,
            self.password,
            self.validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.client)
        self.assertEqual(flavor['vcpus'], linux_client.get_number_of_vcpus())

    @test.idempotent_id('ac1ad47f-984b-4441-9274-c9079b7a0666')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_host_name_is_same_as_server_name(self):
        # Verify the instance host name is the same as the server name
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server),
            self.ssh_user,
            self.password,
            self.validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.client)
        self.assertTrue(linux_client.hostname_equals_servername(self.name))

    @test.idempotent_id('ed20d3fb-9d1f-4329-b160-543fbd5d9811')
    def test_create_server_with_scheduler_hint_group(self):
        # Create a server with the scheduler hint "group".
        name = data_utils.rand_name('server_group')
        policies = ['affinity']
        body = self.server_groups_client.create_server_group(
            name=name, policies=policies)['server_group']
        group_id = body['id']
        self.addCleanup(self.server_groups_client.delete_server_group,
                        group_id)

        hints = {'group': group_id}
        server = self.create_test_server(scheduler_hints=hints,
                                         wait_until='ACTIVE')

        # Check a server is in the group
        server_group = (self.server_groups_client.show_server_group(group_id)
                        ['server_group'])
        self.assertIn(server['id'], server_group['members'])

    @test.idempotent_id('0578d144-ed74-43f8-8e57-ab10dbf9b3c2')
    @testtools.skipUnless(CONF.service_available.neutron,
                          'Neutron service must be available.')
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
        def cleanup_server():
            self.client.delete_server(server_multi_nics['id'])
            waiters.wait_for_server_termination(self.client,
                                                server_multi_nics['id'])

        self.addCleanup(cleanup_server)

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

    @test.idempotent_id('1678d144-ed74-43f8-8e57-ab10dbf9b3c2')
    @testtools.skipUnless(CONF.service_available.neutron,
                          'Neutron service must be available.')
    # The below skipUnless should be removed once Kilo-eol happens.
    @testtools.skipUnless(CONF.compute_feature_enabled.
                          allow_duplicate_networks,
                          'Duplicate networks must be allowed')
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

        def cleanup_server():
            self.client.delete_server(server_multi_nics['id'])
            waiters.wait_for_server_termination(self.client,
                                                server_multi_nics['id'])

        self.addCleanup(cleanup_server)

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


class ServersWithSpecificFlavorTestJSON(base.BaseV2ComputeAdminTest):
    disk_config = 'AUTO'

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServersWithSpecificFlavorTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersWithSpecificFlavorTestJSON, cls).setup_clients()
        cls.flavor_client = cls.os_adm.flavors_client
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        cls.set_validation_resources()

        super(ServersWithSpecificFlavorTestJSON, cls).resource_setup()

    @test.idempotent_id('b3c7bcfc-bb5b-4e22-b517-c7f686b802ca')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_verify_created_server_ephemeral_disk(self):
        # Verify that the ephemeral disk is created when creating server
        flavor_base = self.flavors_client.show_flavor(
            self.flavor_ref)['flavor']

        def create_flavor_with_extra_specs():
            flavor_with_eph_disk_name = data_utils.rand_name('eph_flavor')
            flavor_with_eph_disk_id = data_utils.rand_int_id(start=1000)

            ram = flavor_base['ram']
            vcpus = flavor_base['vcpus']
            disk = flavor_base['disk']

            # Create a flavor with extra specs
            flavor = (self.flavor_client.
                      create_flavor(name=flavor_with_eph_disk_name,
                                    ram=ram, vcpus=vcpus, disk=disk,
                                    id=flavor_with_eph_disk_id,
                                    ephemeral=1))['flavor']
            self.addCleanup(flavor_clean_up, flavor['id'])

            return flavor['id']

        def create_flavor_without_extra_specs():
            flavor_no_eph_disk_name = data_utils.rand_name('no_eph_flavor')
            flavor_no_eph_disk_id = data_utils.rand_int_id(start=1000)

            ram = flavor_base['ram']
            vcpus = flavor_base['vcpus']
            disk = flavor_base['disk']

            # Create a flavor without extra specs
            flavor = (self.flavor_client.
                      create_flavor(name=flavor_no_eph_disk_name,
                                    ram=ram, vcpus=vcpus, disk=disk,
                                    id=flavor_no_eph_disk_id))['flavor']
            self.addCleanup(flavor_clean_up, flavor['id'])

            return flavor['id']

        def flavor_clean_up(flavor_id):
            self.flavor_client.delete_flavor(flavor_id)
            self.flavor_client.wait_for_resource_deletion(flavor_id)

        flavor_with_eph_disk_id = create_flavor_with_extra_specs()
        flavor_no_eph_disk_id = create_flavor_without_extra_specs()

        admin_pass = self.image_ssh_password

        server_no_eph_disk = self.create_test_server(
            validatable=True,
            wait_until='ACTIVE',
            adminPass=admin_pass,
            flavor=flavor_no_eph_disk_id)

        # Get partition number of server without extra specs.
        server_no_eph_disk = self.client.show_server(
            server_no_eph_disk['id'])['server']
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(server_no_eph_disk),
            self.ssh_user,
            admin_pass,
            self.validation_resources['keypair']['private_key'],
            server=server_no_eph_disk,
            servers_client=self.client)
        partition_num = len(linux_client.get_partitions().split('\n'))

        # Explicit server deletion necessary for Juno compatibility
        self.client.delete_server(server_no_eph_disk['id'])

        server_with_eph_disk = self.create_test_server(
            validatable=True,
            wait_until='ACTIVE',
            adminPass=admin_pass,
            flavor=flavor_with_eph_disk_id)

        server_with_eph_disk = self.client.show_server(
            server_with_eph_disk['id'])['server']
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(server_with_eph_disk),
            self.ssh_user,
            admin_pass,
            self.validation_resources['keypair']['private_key'],
            server=server_with_eph_disk,
            servers_client=self.client)
        partition_num_emph = len(linux_client.get_partitions().split('\n'))
        self.assertEqual(partition_num + 1, partition_num_emph)


class ServersTestManualDisk(ServersTestJSON):
    disk_config = 'MANUAL'

    @classmethod
    def skip_checks(cls):
        super(ServersTestManualDisk, cls).skip_checks()
        if not CONF.compute_feature_enabled.disk_config:
            msg = "DiskConfig extension not enabled."
            raise cls.skipException(msg)
