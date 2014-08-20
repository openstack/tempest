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


class ServersTestJSON(base.BaseV2ComputeTest):
    disk_config = 'AUTO'

    @classmethod
    def setUpClass(cls):
        cls.prepare_instance_network()
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

    @test.attr(type='smoke')
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

    def _verify_extended_attributes(self, server):
        mac_addrs = []

        for i in server['addresses']:
            mac_addrs.extend(map(lambda x: x['OS-EXT-IPS-MAC:mac_addr'],
                                 server['addresses'][i]))
        self.assertNotEmpty(mac_addrs)
        # self.assertIn(mac_addr, mac_addrs)
        self.assertEqual(server['OS-DCF:diskConfig'], self.disk_config)
        self.assertIn('OS-EXT-AZ:availability_zone', server)
        self.assertIn('OS-EXT-SRV-ATTR:host', server)
        self.assertIn('OS-EXT-SRV-ATTR:hypervisor_hostname', server)
        self.assertIn('OS-EXT-SRV-ATTR:instance_name', server)
        self.assertIn('OS-EXT-STS:power_state', server)
        self.assertIn('OS-EXT-STS:task_state', server)
        self.assertIn('OS-EXT-STS:vm_state', server)
        self.assertIn('OS-EXT-STS:power_state', server)
        self.assertIn('OS-SRV-USG:launched_at', server)
        self.assertIn('OS-SRV-USG:terminated_at', server)

    @test.attr(type='gate')
    def test_verify_server_extended_attributes(self):

        # Create a test server with extended attributes
        name = data_utils.rand_name('server_test_ext')
        mac_addr = "fa:16:3e:2d:ec:3c"
        file_contents = 'Another test file.'
        personality = [{'path': '/etc/anotest.txt',
                       'contents': base64.b64encode(file_contents)}]
        resp, server = self.create_test_server(name=name,
                                               meta=self.meta,
                                               accessIPv4=self.accessIPv4,
                                               accessIPv6=self.accessIPv6,
                                               personality=personality,
                                               disk_config=self.disk_config,
                                               mac_addr=mac_addr)
        self.addCleanup(self.client.delete_server, server['id'])
        self.client.wait_for_server_status(server['id'], 'ACTIVE')
        resp, body = self.client.get_server(server['id'])

        # Verify the given extended availability zones,
        # extended drive configs, extended status, extended usages,
        # extended mac_addr and other extended attributes
        self._verify_extended_attributes(body)

        # Verify the extended attributes given
        # in the detailed list
        resp, body = self.client.list_servers_with_detail()
        servers = body['servers']

        # Select the first server with specified id
        server = [i for i in servers if i['id'] == server['id']][0]
        self._verify_extended_attributes(server)

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
        linux_client = remote_client.RemoteClient(self.server, self.ssh_user,
                                                  self.password)
        self.assertEqual(flavor['vcpus'], linux_client.get_number_of_vcpus())

    @testtools.skipUnless(CONF.compute.run_ssh,
                          'Instance validation tests are disabled.')
    @test.attr(type='gate')
    def test_host_name_is_same_as_server_name(self):
        # Verify the instance host name is the same as the server name
        linux_client = remote_client.RemoteClient(self.server, self.ssh_user,
                                                  self.password)
        self.assertTrue(linux_client.hostname_equals_servername(self.name))

    @test.skip_because(bug="1306367", interface="xml")
    @test.attr(type='gate')
    def test_create_server_with_scheduler_hint_group(self):
        # Create a server with the scheduler hint "group".
        name = data_utils.rand_name('server_group')
        policies = ['affinity']
        resp, body = self.client.create_server_group(name=name,
                                                     policies=policies)
        self.assertEqual(200, resp.status)
        group_id = body['id']
        self.addCleanup(self.client.delete_server_group, group_id)

        hints = {'group': group_id}
        resp, server = self.create_test_server(sched_hints=hints,
                                               wait_until='ACTIVE')
        self.assertEqual(202, resp.status)

        # Check a server is in the group
        resp, server_group = self.client.get_server_group(group_id)
        self.assertEqual(200, resp.status)
        self.assertIn(server['id'], server_group['members'])

    def _delete_volume(self, volume_id):
        if self.attached:
            self.volumes_client.wait_for_volume_status(volume_id, 'available')

        self.volumes_client.delete_volume(volume_id)
        self.attached = False

    @test.attr(type='gate')
    def test_create_server_with_block_device_mapping(self):
        # Create a test volume
        v_name = data_utils.rand_name('volume')
        metadata = {'Type': 'work'}
        resp, volume = self.volumes_client.create_volume(size=1,
                                                         display_name=v_name,
                                                         metadata=metadata)
        self.addCleanup(self._delete_volume, volume['id'])
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')

        # Create a server with a block device mapping.
        name = data_utils.rand_name('server')
        device_base = CONF.compute.volume_device_name
        # Use the same driver as volume_device_name specified in config
        while str.isdigit(device_base[-1:]):
            device_base = device_base[:-1]
        device_name1 = "/dev/" + device_base[:-1] + "a"
        device_name2 = "/dev/" + device_base[:-1] + "b"

        mapping = [{
                   "device_name": device_name2,
                   "source_type": "blank",
                   "destination_type": "local",
                   "delete_on_termination": "True",
                   "guest_format": "swap",
                   "boot_index": "-1"
                   },
                   {
                   "device_name": device_name1,
                   "source_type": "volume",
                   "destination_type": "volume",
                   "uuid": volume['id'],
                   "boot_index": "0"
                   }]
        resp, server = self.create_test_server(name=name,
                                               meta=metadata,
                                               block_device_mapping_v2=mapping)
        self.assertEqual(202, resp.status)
        self.attached = True
        self.addCleanup(self.client.delete_server, server['id'])
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        resp, server = self.client.get_server(server['id'])
        self.assertIn(volume['id'],
                      map(lambda x: x['id'],
                          server['os-extended-volumes:volumes_attached']))

    @test.attr(type='gate')
    def test_create_server_with_boot_volume(self):
        # Create a test volume
        v_name = data_utils.rand_name('volume')
        resp, volume = self.volumes_client.create_volume(size=1,
                                                         display_name=v_name)
        self.addCleanup(self._delete_volume, volume['id'])
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')

        # Create servers that boots from a volume.
        name = data_utils.rand_name('server')
        device_base = CONF.compute.volume_device_name
        # Use the same driver as volume_device_name specified in config
        while str.isdigit(device_base[-1:]):
            device_base = device_base[:-1]
        device_name = "/dev/" + device_base[:-1] + "b"

        mapping = [{
                   "virtual_name": "root",
                   "device_name": device_name,
                   "volume_id": volume['id'],
                   "delete_on_termination": "False",
                   }]
        resp, server = self.create_test_server(name=name,
                                               min_count=1,
                                               max_count=1,
                                               block_device_mapping=mapping,
                                               volumes_boot=True)
        self.addCleanup(self.client.delete_server, server['id'])
        self.assertEqual(202, resp.status)
        self.attached = True
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        resp, server = self.client.get_server(server['id'])
        self.assertIn(volume['id'],
                      map(lambda x: x['id'],
                          server['os-extended-volumes:volumes_attached']))


class ServersWithSpecificFlavorTestJSON(base.BaseV2ComputeAdminTest):
    disk_config = 'AUTO'

    @classmethod
    def setUpClass(cls):
        cls.prepare_instance_network()
        super(ServersWithSpecificFlavorTestJSON, cls).setUpClass()
        cls.flavor_client = cls.os_adm.flavors_client
        cls.client = cls.servers_client

    @testtools.skipUnless(CONF.compute.run_ssh,
                          'Instance validation tests are disabled.')
    @test.attr(type='gate')
    def test_verify_created_server_ephemeral_disk(self):
        # Verify that the ephemeral disk is created when creating server

        def create_flavor_with_extra_specs():
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
            self.addCleanup(flavor_clean_up, flavor['id'])
            self.assertEqual(200, resp.status)

            return flavor['id']

        def create_flavor_without_extra_specs():
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
            self.addCleanup(flavor_clean_up, flavor['id'])
            self.assertEqual(200, resp.status)

            return flavor['id']

        def flavor_clean_up(flavor_id):
            resp, body = self.flavor_client.delete_flavor(flavor_id)
            self.assertEqual(resp.status, 202)
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
