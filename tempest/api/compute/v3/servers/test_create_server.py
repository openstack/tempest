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

import base64

import netaddr
import testtools

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import test

CONF = config.CONF


class ServersV3Test(base.BaseV3ComputeTest):
    disk_config = 'AUTO'

    @classmethod
    def setUpClass(cls):
        cls.prepare_instance_network()
        super(ServersV3Test, cls).setUpClass()
        cls.meta = {'hello': 'world'}
        cls.accessIPv4 = '1.1.1.1'
        cls.accessIPv6 = '0000:0000:0000:0000:0000:babe:220.12.22.2'
        cls.name = data_utils.rand_name('server')
        file_contents = 'This is a test file.'
        personality = [{'path': '/test.txt',
                       'contents': base64.b64encode(file_contents)}]
        cls.client = cls.servers_client
        cli_resp = cls.create_test_server(name=cls.name,
                                          meta=cls.meta,
                                          access_ip_v4=cls.accessIPv4,
                                          access_ip_v6=cls.accessIPv6,
                                          personality=personality,
                                          disk_config=cls.disk_config)
        cls.resp, cls.server_initial = cli_resp
        cls.password = cls.server_initial['admin_password']
        cls.client.wait_for_server_status(cls.server_initial['id'], 'ACTIVE')
        resp, cls.server = cls.client.get_server(cls.server_initial['id'])

    @test.attr(type='smoke')
    def test_verify_server_details(self):
        # Verify the specified server attributes are set correctly
        self.assertEqual(self.accessIPv4,
                         self.server['os-access-ips:access_ip_v4'])
        # NOTE(maurosr): See http://tools.ietf.org/html/rfc5952 (section 4)
        # Here we compare directly with the canonicalized format.
        self.assertEqual(self.server['os-access-ips:access_ip_v6'],
                         str(netaddr.IPAddress(self.accessIPv6)))
        self.assertEqual(self.name, self.server['name'])
        self.assertEqual(self.image_ref, self.server['image']['id'])
        self.assertEqual(self.flavor_ref, self.server['flavor']['id'])
        self.assertEqual(self.meta, self.server['metadata'])

    @test.attr(type='smoke')
    def test_list_servers(self):
        # The created server should be in the list of all servers
        resp, body = self.client.list_servers()
        servers = body['servers']
        found = any([i for i in servers if i['id'] == self.server['id']])
        self.assertTrue(found)

    @test.attr(type='smoke')
    def test_list_servers_with_detail(self):
        # The created server should be in the detailed list of all servers
        resp, body = self.client.list_servers_with_detail()
        servers = body['servers']
        found = any([i for i in servers if i['id'] == self.server['id']])
        self.assertTrue(found)

    @testtools.skipUnless(CONF.compute.run_ssh,
                          'Instance validation tests are disabled.')
    @test.attr(type='gate')
    def test_verify_created_server_vcpus(self):
        # Verify that the number of vcpus reported by the instance matches
        # the amount stated by the flavor
        resp, flavor = self.flavors_client.get_flavor_details(self.flavor_ref)
        linux_client = remote_client.RemoteClient(self.server,
                                                  self.ssh_user, self.password)
        self.assertEqual(flavor['vcpus'], linux_client.get_number_of_vcpus())

    @testtools.skipUnless(CONF.compute.run_ssh,
                          'Instance validation tests are disabled.')
    @test.attr(type='gate')
    def test_host_name_is_same_as_server_name(self):
        # Verify the instance host name is the same as the server name
        linux_client = remote_client.RemoteClient(self.server,
                                                  self.ssh_user, self.password)
        self.assertTrue(linux_client.hostname_equals_servername(self.name))


class ServersWithSpecificFlavorV3Test(base.BaseV3ComputeAdminTest):
    disk_config = 'AUTO'

    @classmethod
    def setUpClass(cls):
        cls.prepare_instance_network()
        super(ServersWithSpecificFlavorV3Test, cls).setUpClass()
        cls.client = cls.servers_client
        cls.flavor_client = cls.flavors_admin_client

    @testtools.skipUnless(CONF.compute.run_ssh,
                          'Instance validation tests are disabled.')
    @test.attr(type='gate')
    def test_verify_created_server_ephemeral_disk(self):
        # Verify that the ephemeral disk is created when creating server

        def create_flavor_with_extra_specs():
            flavor_with_eph_disk_name = data_utils.rand_name('eph_flavor')
            flavor_with_eph_disk_id = data_utils.rand_int_id(start=1000)
            ram = 512
            vcpus = 1
            disk = 10

            # Create a flavor with extra specs
            resp, flavor = (self.flavor_client.
                            create_flavor(flavor_with_eph_disk_name,
                                          ram, vcpus, disk,
                                          flavor_with_eph_disk_id,
                                          ephemeral=1, rxtx=1))
            self.addCleanup(flavor_clean_up, flavor['id'])
            self.assertEqual(201, resp.status)

            return flavor['id']

        def create_flavor_without_extra_specs():
            flavor_no_eph_disk_name = data_utils.rand_name('no_eph_flavor')
            flavor_no_eph_disk_id = data_utils.rand_int_id(start=1000)

            ram = 512
            vcpus = 1
            disk = 10

            # Create a flavor without extra specs
            resp, flavor = (self.flavor_client.
                            create_flavor(flavor_no_eph_disk_name,
                                          ram, vcpus, disk,
                                          flavor_no_eph_disk_id))
            self.addCleanup(flavor_clean_up, flavor['id'])
            self.assertEqual(201, resp.status)

            return flavor['id']

        def flavor_clean_up(flavor_id):
            resp, body = self.flavor_client.delete_flavor(flavor_id)
            self.assertEqual(resp.status, 204)
            self.flavor_client.wait_for_resource_deletion(flavor_id)

        flavor_with_eph_disk_id = create_flavor_with_extra_specs()
        flavor_no_eph_disk_id = create_flavor_without_extra_specs()

        admin_pass = self.image_ssh_password

        resp, server_no_eph_disk = (self.create_test_server(
                                    wait_until='ACTIVE',
                                    adminPass=admin_pass,
                                    flavor=flavor_no_eph_disk_id))
        resp, server_with_eph_disk = (self.create_test_server(
                                      wait_until='ACTIVE',
                                      adminPass=admin_pass,
                                      flavor=flavor_with_eph_disk_id))
        # Get partition number of server without extra specs.
        _, server_no_eph_disk = self.client.get_server(
            server_no_eph_disk['id'])
        linux_client = remote_client.RemoteClient(server_no_eph_disk,
                                                  self.ssh_user, admin_pass)
        partition_num = len(linux_client.get_partitions().split('\n'))
        _, server_with_eph_disk = self.client.get_server(
            server_with_eph_disk['id'])
        linux_client = remote_client.RemoteClient(server_with_eph_disk,
                                                  self.ssh_user, admin_pass)
        partition_num_emph = len(linux_client.get_partitions().split('\n'))
        self.assertEqual(partition_num + 1, partition_num_emph)


class ServersV3TestManualDisk(ServersV3Test):
    disk_config = 'MANUAL'

    @classmethod
    def setUpClass(cls):
        if not CONF.compute_feature_enabled.disk_config:
            msg = "DiskConfig extension not enabled."
            raise cls.skipException(msg)
        super(ServersV3TestManualDisk, cls).setUpClass()
