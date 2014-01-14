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
from tempest.common.utils.linux.remote_client import RemoteClient
from tempest import config
from tempest.test import attr

CONF = config.CONF


class ServersTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'
    run_ssh = CONF.compute.run_ssh
    disk_config = 'AUTO'

    @classmethod
    def setUpClass(cls):
        super(ServersTestJSON, cls).setUpClass()
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
                                          accessIPv4=cls.accessIPv4,
                                          accessIPv6=cls.accessIPv6,
                                          personality=personality,
                                          disk_config=cls.disk_config)
        cls.resp, cls.server_initial = cli_resp
        cls.password = cls.server_initial['adminPass']
        cls.client.wait_for_server_status(cls.server_initial['id'], 'ACTIVE')
        resp, cls.server = cls.client.get_server(cls.server_initial['id'])

    @attr(type='smoke')
    def test_create_server_response(self):
        # Check that the required fields are returned with values
        self.assertEqual(202, self.resp.status)
        self.assertTrue(self.server_initial['id'] is not None)
        self.assertTrue(self.server_initial['adminPass'] is not None)

    @attr(type='smoke')
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

    @attr(type='smoke')
    def test_list_servers(self):
        # The created server should be in the list of all servers
        resp, body = self.client.list_servers()
        servers = body['servers']
        found = any([i for i in servers if i['id'] == self.server['id']])
        self.assertTrue(found)

    @attr(type='smoke')
    def test_list_servers_with_detail(self):
        # The created server should be in the detailed list of all servers
        resp, body = self.client.list_servers_with_detail()
        servers = body['servers']
        found = any([i for i in servers if i['id'] == self.server['id']])
        self.assertTrue(found)

    @testtools.skipIf(not run_ssh, 'Instance validation tests are disabled.')
    @attr(type='gate')
    def test_verify_created_server_vcpus(self):
        # Verify that the number of vcpus reported by the instance matches
        # the amount stated by the flavor
        resp, flavor = self.flavors_client.get_flavor_details(self.flavor_ref)
        linux_client = RemoteClient(self.server, self.ssh_user, self.password)
        self.assertEqual(flavor['vcpus'], linux_client.get_number_of_vcpus())

    @testtools.skipIf(not run_ssh, 'Instance validation tests are disabled.')
    @attr(type='gate')
    def test_host_name_is_same_as_server_name(self):
        # Verify the instance host name is the same as the server name
        linux_client = RemoteClient(self.server, self.ssh_user, self.password)
        self.assertTrue(linux_client.hostname_equals_servername(self.name))


class ServersWithSpecificFlavorTestJSON(base.BaseV2ComputeAdminTest):
    _interface = 'json'
    run_ssh = CONF.compute.run_ssh
    disk_config = 'AUTO'

    @classmethod
    def setUpClass(cls):
        super(ServersWithSpecificFlavorTestJSON, cls).setUpClass()
        cls.meta = {'hello': 'world'}
        cls.accessIPv4 = '1.1.1.1'
        cls.accessIPv6 = '0000:0000:0000:0000:0000:babe:220.12.22.2'
        cls.name = data_utils.rand_name('server')
        file_contents = 'This is a test file.'
        personality = [{'path': '/test.txt',
                       'contents': base64.b64encode(file_contents)}]
        cls.client = cls.servers_client
        cls.flavor_client = cls.os_adm.flavors_client
        cli_resp = cls.create_test_server(name=cls.name,
                                          meta=cls.meta,
                                          accessIPv4=cls.accessIPv4,
                                          accessIPv6=cls.accessIPv6,
                                          personality=personality,
                                          disk_config=cls.disk_config)
        cls.resp, cls.server_initial = cli_resp
        cls.password = cls.server_initial['adminPass']
        cls.client.wait_for_server_status(cls.server_initial['id'], 'ACTIVE')
        resp, cls.server = cls.client.get_server(cls.server_initial['id'])

    @testtools.skipIf(not run_ssh, 'Instance validation tests are disabled.')
    @attr(type='gate')
    def test_verify_created_server_ephemeral_disk(self):
        # Verify that the ephemeral disk is created when creating server

        def create_flavor_with_extra_specs(self):
            flavor_with_eph_disk_name = data_utils.rand_name('eph_flavor')
            flavor_with_eph_disk_id = data_utils.rand_int_id(start=1000)
            ram = 64
            vcpus = 1
            disk = 0

            # Create a flavor with extra specs
            resp, flavor = (self.flavor_client.
                            create_flavor(flavor_with_eph_disk_name,
                                          ram, vcpus, disk,
                                          flavor_with_eph_disk_id,
                                          ephemeral=1))
            self.addCleanup(self.flavor_clean_up, flavor['id'])
            self.assertEqual(200, resp.status)

            return flavor['id']

        def create_flavor_without_extra_specs(self):
            flavor_no_eph_disk_name = data_utils.rand_name('no_eph_flavor')
            flavor_no_eph_disk_id = data_utils.rand_int_id(start=1000)

            ram = 64
            vcpus = 1
            disk = 0

            # Create a flavor without extra specs
            resp, flavor = (self.flavor_client.
                            create_flavor(flavor_no_eph_disk_name,
                                          ram, vcpus, disk,
                                          flavor_no_eph_disk_id))
            self.addCleanup(self.flavor_clean_up, flavor['id'])
            self.assertEqual(200, resp.status)

            return flavor['id']

        def flavor_clean_up(self, flavor_id):
            resp, body = self.flavor_client.delete_flavor(flavor_id)
            self.assertEqual(resp.status, 202)
            self.flavor_client.wait_for_resource_deletion(flavor_id)

        flavor_with_eph_disk_id = self.create_flavor_with_extra_specs()
        flavor_no_eph_disk_id = self.create_flavor_without_extra_specs()

        admin_pass = self.image_ssh_password

        resp, server_no_eph_disk = (self.
                                    create_test_server(
                                    wait_until='ACTIVE',
                                    adminPass=admin_pass,
                                    flavor=flavor_no_eph_disk_id))
        resp, server_with_eph_disk = (self.create_test_server(
                                      wait_until='ACTIVE',
                                      adminPass=admin_pass,
                                      flavor=flavor_with_eph_disk_id))
        # Get partition number of server without extra specs.
        linux_client = RemoteClient(server_no_eph_disk,
                                    self.ssh_user, self.password)
        partition_num = len(linux_client.get_partitions())

        linux_client = RemoteClient(server_with_eph_disk,
                                    self.ssh_user, self.password)
        self.assertEqual(partition_num + 1, linux_client.get_partitions())


class ServersTestManualDisk(ServersTestJSON):
    disk_config = 'MANUAL'

    @classmethod
    def setUpClass(cls):
        if not CONF.compute_feature_enabled.disk_config:
            msg = "DiskConfig extension not enabled."
            raise cls.skipException(msg)
        super(ServersTestManualDisk, cls).setUpClass()


class ServersTestXML(ServersTestJSON):
    _interface = 'xml'


class ServersWithSpecificFlavorTestXML(ServersWithSpecificFlavorTestJSON):
    _interface = 'xml'
