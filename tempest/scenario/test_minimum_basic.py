# Copyright 2013 NEC Corporation
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

import testtools

from tempest.common import custom_matchers
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest.scenario import manager

CONF = config.CONF


class TestMinimumBasicScenario(manager.ScenarioTest):

    """This is a basic minimum scenario test.

    These tests below:
    * across the multiple components
    * as a regular user
    * with and without optional parameters
    * check command outputs
    """

    def nova_show(self, server):
        got_server = (self.servers_client.show_server(server['id'])
                      ['server'])
        excluded_keys = ['OS-EXT-AZ:availability_zone']
        # Exclude these keys because of LP:#1486475
        excluded_keys.extend(['OS-EXT-STS:power_state', 'updated'])
        self.assertThat(
            server, custom_matchers.MatchesDictExceptForKeys(
                got_server, excluded_keys=excluded_keys))

    def cinder_show(self, volume):
        got_volume = self.volumes_client.show_volume(volume['id'])['volume']
        # Exclude updated_at because of bug 1838202.
        excluded_keys = ['updated_at']
        self.assertThat(
            volume, custom_matchers.MatchesDictExceptForKeys(
                got_volume, excluded_keys=excluded_keys))

    def nova_reboot(self, server, hard=False):
        self.servers_client.reboot_server(server['id'],
                                          type="HARD" if hard else "SOFT")
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')

    def check_disks(self):
        # NOTE(andreaf) The device name may be different on different guest OS
        disks = self.linux_client.get_disks()
        self.assertEqual(1, disks.count(CONF.compute.volume_device_name))

    def create_and_add_security_group_to_server(self, server):
        secgroup = self.create_security_group()
        self.servers_client.add_security_group(server['id'],
                                               name=secgroup['name'])
        self.addCleanup(self.servers_client.remove_security_group,
                        server['id'], name=secgroup['name'])

        def wait_for_secgroup_add():
            body = (self.servers_client.show_server(server['id'])
                    ['server'])
            return {'name': secgroup['name']} in body['security_groups']

        if not test_utils.call_until_true(wait_for_secgroup_add,
                                          CONF.compute.build_timeout,
                                          CONF.compute.build_interval):
            msg = ('Timed out waiting for adding security group %s to server '
                   '%s' % (secgroup['id'], server['id']))
            raise exceptions.TimeoutException(msg)

    def _get_floating_ip_in_server_addresses(self, floating_ip, server):
        for addresses in server['addresses'].values():
            for address in addresses:
                if (address['OS-EXT-IPS:type'] == 'floating' and
                        address['addr'] == floating_ip['floating_ip_address']):
                    return address

    def _is_floating_ip_detached_from_server(self, server, floating_ip):
        server_info = self.servers_client.show_server(
            server['id'])['server']
        address = self._get_floating_ip_in_server_addresses(
            floating_ip, server_info)
        return (not address)

    @decorators.idempotent_id('bdbb5441-9204-419d-a225-b4fdbfb1a1a8')
    @utils.services('compute', 'volume', 'image', 'network')
    def test_minimum_basic_scenario(self):
        """This is a basic minimum scenario with multiple components

        Steps:
        1. Create image
        2. Create keypair
        3. Boot instance with keypair and get list of instances
        4. Create volume and show list of volumes
        5. Attach volume to instance and getlist of volumes
        6. Add IP to instance
        7. Create and add security group to instance
        8. Check SSH connection to instance
        9. Reboot instance
        10. Check SSH connection to instance after reboot
        """
        image = self.image_create()
        keypair = self.create_keypair()

        server = self.create_server(image_id=image, validatable=True, wait_until="SSHABLE", key_name=keypair['name'])
        servers = self.servers_client.list_servers()['servers']
        self.assertIn(server['id'], [x['id'] for x in servers])

        self.nova_show(server)

        volume = self.create_volume()
        volumes = self.volumes_client.list_volumes()['volumes']
        self.assertIn(volume['id'], [x['id'] for x in volumes])

        self.cinder_show(volume)

        volume = self.nova_volume_attach(server, volume)
        self.addCleanup(self.nova_volume_detach, server, volume)
        self.cinder_show(volume)

        floating_ip = None
        server = self.servers_client.show_server(server['id'])['server']
        if (CONF.network_feature_enabled.floating_ips and
                CONF.network.floating_network_name):
            fip = self.create_floating_ip(server)
            floating_ip = self.associate_floating_ip(
                fip, server)
            waiters.wait_for_server_floating_ip(self.servers_client,
                                                server, floating_ip)
            ssh_ip = floating_ip['floating_ip_address']
        else:
            ssh_ip = self.get_server_ip(server)

        self.create_and_add_security_group_to_server(server)

        # check that we can SSH to the server before reboot
        self.linux_client = self.get_remote_client(
            ssh_ip, private_key=keypair['private_key'],
            server=server)

        self.nova_reboot(server)

        # check that we can SSH to the server after reboot
        # (both connections are part of the scenario)
        self.linux_client = self.get_remote_client(
            ssh_ip, private_key=keypair['private_key'],
            server=server)

        self.check_disks()

        if floating_ip:
            # delete the floating IP, this should refresh the server addresses
            self.disassociate_floating_ip(floating_ip)
            waiters.wait_for_server_floating_ip(
                self.servers_client, server, floating_ip,
                wait_for_disassociate=True)

            if not test_utils.call_until_true(
                    self._is_floating_ip_detached_from_server,
                    CONF.compute.build_timeout,
                    CONF.compute.build_interval, server, floating_ip):
                msg = ("Floating IP '%s' should not be in server addresses: %s"
                       % (floating_ip['floating_ip_address'],
                          server['addresses']))
                raise exceptions.TimeoutException(msg)

    @decorators.idempotent_id('a8fd48ec-1d01-4895-b932-02321661ec1e')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          "Cinder volume snapshots are disabled")
    @utils.services('compute', 'volume', 'image', 'network')
    def test_minimum_basic_instance_hard_reboot_after_vol_snap_deletion(self):
        """Test compute hard reboot after volume snapshot deleted

        Steps:
        1. Create image
        2. Create keypair
        3. Boot instance with keypair and get list of instances
        4. Create volume and show list of volumes
        5. Attach volume to instance and getlist of volumes
        6. Create a snapshot from volume
        7. Add IP to instance
        8. Create and add security group to instance
        9. Check SSH connection to instance
        10. Write data timestamp to the attached volume
        11. Delete volume snapshot before reboot instance
        12. Reboot instance (HARD)
        13. Check SSH connection to instance after reboot
        14. Verify attached disk data timestamp post instance reboot
        """
        image = self.image_create()
        keypair = self.create_keypair()

        server = self.create_server(image_id=image, key_name=keypair['name'])
        servers = self.servers_client.list_servers()['servers']
        self.assertIn(server['id'], [x['id'] for x in servers])

        self.nova_show(server)

        volume = self.create_volume()
        volumes = self.volumes_client.list_volumes()['volumes']
        self.assertIn(volume['id'], [x['id'] for x in volumes])

        self.cinder_show(volume)

        volume = self.nova_volume_attach(server, volume)
        self.addCleanup(self.nova_volume_detach, server, volume)
        snapshot = self.create_volume_snapshot(volume['id'], force=True)
        self.cinder_show(volume)

        floating_ip = None
        server = self.servers_client.show_server(server['id'])['server']
        if (CONF.network_feature_enabled.floating_ips and
                CONF.network.floating_network_name):
            fip = self.create_floating_ip(server)
            floating_ip = self.associate_floating_ip(
                fip, server)
            # fetch the server again to make sure the addresses were refreshed
            # after associating the floating IP
            server = self.servers_client.show_server(server['id'])['server']
            address = self._get_floating_ip_in_server_addresses(
                floating_ip, server)
            self.assertIsNotNone(
                address,
                "Failed to find floating IP '%s' in server addresses: %s" %
                (floating_ip['floating_ip_address'], server['addresses']))
            ssh_ip = floating_ip['floating_ip_address']
        else:
            ssh_ip = self.get_server_ip(server)

        self.create_and_add_security_group_to_server(server)

        # check that we can SSH to the server before reboot
        self.linux_client = self.get_remote_client(
            ssh_ip, private_key=keypair['private_key'],
            server=server)

        # write data to the volume before reboot instance
        timestamp_before = self.create_timestamp(
            ssh_ip, private_key=keypair['private_key'], server=server)
        # delete the snapshot before rebooting the instance
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])
        self.nova_reboot(server, hard=True)

        # check that we can SSH to the server after reboot
        # (both connections are part of the scenario)
        self.linux_client = self.get_remote_client(
            ssh_ip, private_key=keypair['private_key'],
            server=server)

        self.check_disks()
        timestamp_after = self.get_timestamp(
            ssh_ip, private_key=keypair['private_key'], server=server)
        self.assertEqual(timestamp_before, timestamp_after)
        if floating_ip:
            # delete the floating IP, this should refresh the server addresses
            self.disassociate_floating_ip(floating_ip)
            waiters.wait_for_server_floating_ip(
                self.servers_client, server, floating_ip,
                wait_for_disassociate=True)

            if not test_utils.call_until_true(
                self._is_floating_ip_detached_from_server,
                    CONF.compute.build_timeout, CONF.compute.build_interval,
                    server, floating_ip):
                msg = ("Floating IP '%s' should not be in server addresses: %s"
                       % (floating_ip['floating_ip_address'],
                          server['addresses']))
                raise exceptions.TimeoutException(msg)
