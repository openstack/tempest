# Copyright (C) 2016, Red Hat, Inc.
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

import json

from oslo_log import log as logging

from tempest.api.compute import base
from tempest.common import utils
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions


CONF = config.CONF

LOG = logging.getLogger(__name__)


class DeviceTaggingTest(base.BaseV2ComputeTest):

    min_microversion = '2.32'
    # NOTE(mriedem): max_version looks odd but it's actually correct. Due to a
    # bug in the 2.32 microversion, tags on block devices only worked with the
    # 2.32 microversion specifically. And tags on networks only worked between
    # 2.32 and 2.36 inclusive; the 2.37 microversion broke tags for networks.
    max_microversion = '2.32'

    @classmethod
    def skip_checks(cls):
        super(DeviceTaggingTest, cls).skip_checks()
        if not CONF.service_available.neutron:
            raise cls.skipException('Neutron is required')
        if not CONF.validation.run_validation:
            raise cls.skipException('Validation must be enabled')
        if (not CONF.compute_feature_enabled.config_drive
            and not CONF.compute_feature_enabled.metadata_service):
            raise cls.skipException('One of metadata or config drive must be '
                                    'enabled')

    @classmethod
    def setup_clients(cls):
        super(DeviceTaggingTest, cls).setup_clients()
        cls.networks_client = cls.os_primary.networks_client
        cls.ports_client = cls.os_primary.ports_client
        cls.subnets_client = cls.os_primary.subnets_client
        cls.interfaces_client = cls.os_primary.interfaces_client

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources(network=True, subnet=True, router=True,
                                  dhcp=True)
        super(DeviceTaggingTest, cls).setup_credentials()

    def verify_device_metadata(self, md_json):
        md_dict = json.loads(md_json)
        for d in md_dict['devices']:
            if d['type'] == 'nic':
                if d['mac'] == self.port1['mac_address']:
                    self.assertEqual(d['tags'], ['port-1'])
                if d['mac'] == self.port2['mac_address']:
                    self.assertEqual(d['tags'], ['port-2'])
                if d['mac'] == self.net_2_100_mac:
                    self.assertEqual(d['tags'], ['net-2-100'])
                if d['mac'] == self.net_2_200_mac:
                    self.assertEqual(d['tags'], ['net-2-200'])

            # A hypervisor may present multiple paths to a tagged disk, so
            # there may be duplicated tags in the metadata, use set() to
            # remove duplicated tags.
            found_devices = [d['tags'][0] for d in md_dict['devices']]
            self.assertEqual(set(found_devices), set(['port-1', 'port-2',
                                                      'net-1', 'net-2-100',
                                                      'net-2-200', 'boot',
                                                      'other']))

    @decorators.idempotent_id('a2e65a6c-66f1-4442-aaa8-498c31778d96')
    @utils.services('network', 'volume', 'image')
    def test_device_tagging(self):
        # Create volumes
        # The create_volume methods waits for the volumes to be available and
        # the base class will clean them up on tearDown.
        boot_volume = self.create_volume(CONF.compute.image_ref)
        other_volume = self.create_volume()
        untagged_volume = self.create_volume()

        # Create networks
        net1 = self.networks_client.create_network(
            name=data_utils.rand_name('device-tagging-net1'))['network']
        self.addCleanup(self.networks_client.delete_network, net1['id'])

        net2 = self.networks_client.create_network(
            name=data_utils.rand_name('device-tagging-net2'))['network']
        self.addCleanup(self.networks_client.delete_network, net2['id'])

        # Create subnets
        subnet1 = self.subnets_client.create_subnet(
            network_id=net1['id'],
            cidr='10.1.1.0/24',
            ip_version=4)['subnet']
        self.addCleanup(self.subnets_client.delete_subnet, subnet1['id'])

        subnet2 = self.subnets_client.create_subnet(
            network_id=net2['id'],
            cidr='10.2.2.0/24',
            ip_version=4)['subnet']
        self.addCleanup(self.subnets_client.delete_subnet, subnet2['id'])

        # Create ports
        self.port1 = self.ports_client.create_port(
            network_id=net1['id'],
            fixed_ips=[{'subnet_id': subnet1['id']}])['port']
        self.addCleanup(self.ports_client.delete_port, self.port1['id'])

        self.port2 = self.ports_client.create_port(
            network_id=net1['id'],
            fixed_ips=[{'subnet_id': subnet1['id']}])['port']
        self.addCleanup(self.ports_client.delete_port, self.port2['id'])

        # Create server
        admin_pass = data_utils.rand_password()
        config_drive_enabled = CONF.compute_feature_enabled.config_drive
        validation_resources = self.get_test_validation_resources(
            self.os_primary)

        server = self.create_test_server(
            validatable=True,
            wait_until='ACTIVE',
            validation_resources=validation_resources,
            config_drive=config_drive_enabled,
            adminPass=admin_pass,
            name=data_utils.rand_name('device-tagging-server'),
            networks=[
                # Validation network for ssh
                {
                    'uuid': self.get_tenant_network()['id']
                },
                # Different tags for different ports
                {
                    'port': self.port1['id'],
                    'tag': 'port-1'
                },
                {
                    'port': self.port2['id'],
                    'tag': 'port-2'
                },
                # Two nics on same net, one tagged one not
                {
                    'uuid': net1['id'],
                    'tag': 'net-1'
                },
                {
                    'uuid': net1['id']
                },
                # Two nics on same net, different IP
                {
                    'uuid': net2['id'],
                    'fixed_ip': '10.2.2.100',
                    'tag': 'net-2-100'
                },
                {
                    'uuid': net2['id'],
                    'fixed_ip': '10.2.2.200',
                    'tag': 'net-2-200'
                }
            ],
            block_device_mapping_v2=[
                # Boot volume
                {
                    'uuid': boot_volume['id'],
                    'source_type': 'volume',
                    'destination_type': 'volume',
                    'boot_index': 0,
                    'tag': 'boot'
                },
                # Other volume
                {
                    'uuid': other_volume['id'],
                    'source_type': 'volume',
                    'destination_type': 'volume',
                    'boot_index': 1,
                    'tag': 'other'
                },
                # Untagged volume
                {
                    'uuid': untagged_volume['id'],
                    'source_type': 'volume',
                    'destination_type': 'volume',
                    'boot_index': 2
                }
            ])

        self.addCleanup(self.delete_server, server['id'])

        server = self.servers_client.show_server(server['id'])['server']
        self.ssh_client = remote_client.RemoteClient(
            self.get_server_ip(server, validation_resources),
            CONF.validation.image_ssh_user,
            admin_pass,
            validation_resources['keypair']['private_key'],
            server=server,
            servers_client=self.servers_client)

        # Find the MAC addresses of our fixed IPs
        self.net_2_100_mac = None
        self.net_2_200_mac = None
        ifaces = self.interfaces_client.list_interfaces(server['id'])
        for iface in ifaces['interfaceAttachments']:
            if 'fixed_ips' in iface:
                for ip in iface['fixed_ips']:
                    if ip['ip_address'] == '10.2.2.100':
                        self.net_2_100_mac = iface['mac_addr']
                    if ip['ip_address'] == '10.2.2.200':
                        self.net_2_200_mac = iface['mac_addr']
        # Make sure we have the MACs we need, there's no reason for some to be
        # missing
        self.assertTrue(self.net_2_100_mac)
        self.assertTrue(self.net_2_200_mac)

        # Verify metadata from metadata service
        if CONF.compute_feature_enabled.metadata_service:
            md_url = 'http://169.254.169.254/openstack/latest/meta_data.json'
            LOG.info('Attempting to verify tagged devices in server %s via '
                     'the metadata service: %s', server['id'], md_url)

            def get_and_verify_metadata():
                try:
                    self.ssh_client.exec_command('curl -V')
                except exceptions.SSHExecCommandFailed:
                    if not CONF.compute_feature_enabled.config_drive:
                        raise self.skipException('curl not found in guest '
                                                 'and config drive is '
                                                 'disabled')
                    LOG.warning('curl was not found in the guest, device '
                                'tagging metadata was not checked in the '
                                'metadata API')
                    return True
                cmd = 'curl %s' % md_url
                md_json = self.ssh_client.exec_command(cmd)
                self.verify_device_metadata(md_json)
                return True

            if not test_utils.call_until_true(get_and_verify_metadata,
                                              CONF.compute.build_timeout,
                                              CONF.compute.build_interval):
                raise exceptions.TimeoutException('Timeout while verifying '
                                                  'metadata on server.')

        # Verify metadata on config drive
        if CONF.compute_feature_enabled.config_drive:
            cmd_blkid = 'blkid -t LABEL=config-2 -o device'
            LOG.info('Attempting to verify tagged devices in server %s via '
                     'the config drive.', server['id'])
            dev_name = self.ssh_client.exec_command(cmd_blkid)
            dev_name = dev_name.rstrip()
            try:
                self.ssh_client.exec_command('sudo mount %s /mnt' % dev_name)
            except exceptions.SSHExecCommandFailed:
                # So the command failed, let's try to know why and print some
                # useful information.
                lsblk = self.ssh_client.exec_command('sudo lsblk --fs --ascii')
                LOG.error("Mounting %s on /mnt failed. Right after the "
                          "failure 'lsblk' in the guest reported:\n%s",
                          dev_name, lsblk)
                raise

            cmd_md = 'sudo cat /mnt/openstack/latest/meta_data.json'
            md_json = self.ssh_client.exec_command(cmd_md)
            self.verify_device_metadata(md_json)


class DeviceTaggingTestV2_42(DeviceTaggingTest):
    min_microversion = '2.42'
    max_microversion = 'latest'
