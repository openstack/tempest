# Copyright 2024 Openstack Foundation
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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
import time

from oslo_log import log as logging

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest.scenario import manager


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestInstancesWithCinderVolumes(manager.ScenarioTest):
    """This is cinder volumes test.

    Tests are below:
    * test_instances_with_cinder_volumes_on_all_compute_nodes
    """

    compute_min_microversion = '2.60'

    @decorators.idempotent_id('d0e3c1a3-4b0a-4b0e-8b0a-4b0e8b0a4b0e')
    @decorators.attr(type=['slow', 'multinode'])
    @utils.services('compute', 'volume', 'image', 'network')
    def test_instances_with_cinder_volumes_on_all_compute_nodes(self):
        """Test instances with cinder volumes launches on all compute nodes

        Steps:
            1. Create an image
            2. Create a keypair
            3. Create a bootable volume from the image and of the given volume
               type
            4. Boot an instance from the bootable volume on each available
               compute node, up to CONF.compute.min_compute_nodes
            5. Create a volume using each volume_types_for_data_volume on all
               available compute nodes, up to CONF.compute.min_compute_nodes.
               Total number of volumes is equal to
               compute nodes * len(volume_types_for_data_volume)
            6. Assign floating IP to all instances
            7. Configure security group for ssh access to all instances
            8. Confirm ssh access to all instances
            9. Attach volumes to the instances; fixup device mapping if
               required
            10. Run write test to all volumes through ssh connection per
                instance
            11. Clean up the sources, an instance, volumes, keypair and image
        """
        boot_volume_type = (CONF.volume.volume_type or
                            self.create_volume_type()['name'])

        # create an image
        image = self.image_create()

        # create keypair
        keypair = self.create_keypair()

        # check all available zones for booting instances
        available_zone = \
            self.os_admin.availability_zone_client.list_availability_zones(
                detail=True)['availabilityZoneInfo']

        hosts = []
        for zone in available_zone:
            if zone['zoneState']['available']:
                for host in zone['hosts']:
                    if 'nova-compute' in zone['hosts'][host] and \
                        zone['hosts'][host]['nova-compute']['available'] and \
                        CONF.compute.target_hosts_to_avoid not in host:
                        hosts.append({'zone': zone['zoneName'],
                                      'host_name': host})

        # fail if there is less hosts than minimal number of instances
        if len(hosts) < CONF.compute.min_compute_nodes:
            raise exceptions.InvalidConfiguration(
                "Host list %s is shorter than min_compute_nodes. " % hosts)

        # get volume types
        volume_types = []
        if CONF.volume_feature_enabled.volume_types_for_data_volume:
            types = CONF.volume_feature_enabled.volume_types_for_data_volume
            volume_types = types.split(',')
        else:
            # no user specified volume types, create 2 default ones
            volume_types.append(self.create_volume_type()['name'])
            volume_types.append(self.create_volume_type()['name'])

        hosts_to_boot_servers = hosts[:CONF.compute.min_compute_nodes]
        LOG.debug("List of hosts selected to boot servers %s: ",
                  hosts_to_boot_servers)

        # create volumes so that we dont need to wait for them to be created
        # and save them in a list
        created_volumes = []
        for host in hosts_to_boot_servers:
            for volume_type in volume_types:
                created_volumes.append(
                    self.create_volume(volume_type=volume_type,
                                       wait_until=None)
                )

        bootable_volumes = []
        for host in hosts_to_boot_servers:
            # create boot volume from image and of the given volume type
            bootable_volumes.append(
                self.create_volume(
                    imageRef=image, volume_type=boot_volume_type,
                    wait_until=None)
            )

        # boot server
        servers = []

        for bootable_volume in bootable_volumes:

            # wait for bootable volumes to become available
            waiters.wait_for_volume_resource_status(
                self.volumes_client, bootable_volume['id'], 'available')

            # create an instance from bootable volume
            server = self.boot_instance_from_resource(
                source_id=bootable_volume['id'],
                source_type='volume',
                keypair=keypair,
                wait_until=None
            )
            servers.append(server)

        start = 0
        end = len(volume_types)
        for server in servers:
            # wait for server to become active
            waiters.wait_for_server_status(self.servers_client,
                                           server['id'], 'ACTIVE')

            # assign floating ip
            floating_ip = None
            if (CONF.network_feature_enabled.floating_ips and
                CONF.network.floating_network_name):
                fip = self.create_floating_ip(server)
                floating_ip = self.associate_floating_ip(
                    fip, server)
                ssh_ip = floating_ip['floating_ip_address']
            else:
                ssh_ip = self.get_server_ip(server)

            # create security group
            self.create_and_add_security_group_to_server(server)

            # confirm ssh access
            self.linux_client = self.get_remote_client(
                ssh_ip, private_key=keypair['private_key'],
                server=server
            )

            # attach volumes to the instances
            attached_volumes = []
            for volume in created_volumes[start:end]:
                attached_volume, actual_dev = self._attach_fixup(
                    server, volume)
                attached_volumes.append((attached_volume, actual_dev))
                LOG.debug("Attached volume %s to server %s",
                          attached_volume['id'], server['id'])

            server_name = server['name'].split('-')[-1]

            # run write test on all volumes
            for volume, dev_name in attached_volumes:
                mount_path = f"/mnt/{server_name}"

                timestamp_before = self.create_timestamp(
                    ssh_ip, private_key=keypair['private_key'], server=server,
                    dev_name=dev_name, mount_path=mount_path,
                )
                timestamp_after = self.get_timestamp(
                    ssh_ip, private_key=keypair['private_key'], server=server,
                    dev_name=dev_name, mount_path=mount_path,
                )
                self.assertEqual(timestamp_before, timestamp_after)

                # delete volume
                self.nova_volume_detach(server, volume)
                self.volumes_client.delete_volume(volume['id'])

            if floating_ip:
                # delete the floating IP, this should refresh the server
                # addresses
                self.disassociate_floating_ip(floating_ip)
                waiters.wait_for_server_floating_ip(
                    self.servers_client, server, floating_ip,
                    wait_for_disassociate=True)

            start += len(volume_types)
            end += len(volume_types)

    def _attach_fixup(self, server, volume):
        """Attach a volume to the server and update the device key with the
        device actually created inside the guest.
        """
        waiters.wait_for_volume_resource_status(
            self.volumes_client, volume['id'], 'available')

        list_blks = "lsblk --nodeps --noheadings --output NAME"

        blks_before = set(self.linux_client.exec_command(
            list_blks).strip().splitlines())

        attached_volume = self.nova_volume_attach(server, volume)
        # dev name volume['attachments'][0]['device'][5:] is like
        # /dev/vdb, we need to remove /dev/ -> first 5 chars
        dev_name = attached_volume['attachments'][0]['device'][5:]

        retry = 0
        actual_dev = None
        blks_now = set()
        while retry < 4 and not actual_dev:
            try:
                blks_now = set(self.linux_client.exec_command(
                    list_blks).strip().splitlines())
                for blk_dev in (blks_now - blks_before):
                    serial = self.linux_client.exec_command(
                        f"cat /sys/block/{blk_dev}/serial")
                    if serial == volume['id'][:len(serial)]:
                        actual_dev = blk_dev
                        break
            except exceptions.SSHExecCommandFailed:
                retry += 1
                time.sleep(2 ** retry)

        if not actual_dev and len(blks_now - blks_before):
            LOG.warning("Detected new devices in guest but could not match any"
                        f" of them with the volume {volume['id']}")

        if actual_dev and dev_name != actual_dev:
            LOG.info(
                f"OpenStack mapping {volume['id']} to device {dev_name}" +
                f" is actually {actual_dev} inside the guest")
            dev_name = actual_dev

        return attached_volume, dev_name
