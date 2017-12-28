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

import testtools

from tempest.api.compute import base
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

CONF = config.CONF


class ServersWithSpecificFlavorTestJSON(base.BaseV2ComputeAdminTest):
    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServersWithSpecificFlavorTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersWithSpecificFlavorTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @decorators.idempotent_id('b3c7bcfc-bb5b-4e22-b517-c7f686b802ca')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_verify_created_server_ephemeral_disk(self):
        # Verify that the ephemeral disk is created when creating server
        flavor_base = self.flavors_client.show_flavor(
            self.flavor_ref)['flavor']

        def create_flavor_with_ephemeral(ephem_disk):
            name = 'flavor_with_ephemeral_%s' % ephem_disk
            flavor_name = data_utils.rand_name(name)

            ram = flavor_base['ram']
            vcpus = flavor_base['vcpus']
            disk = flavor_base['disk']

            # Create a flavor with ephemeral disk
            flavor = self.create_flavor(name=flavor_name, ram=ram, vcpus=vcpus,
                                        disk=disk, ephemeral=ephem_disk)

            # Set extra specs same as self.flavor_ref for the created flavor,
            # because the environment may need some special extra specs to
            # create server which should have been contained in
            # self.flavor_ref.
            extra_spec_keys = \
                self.admin_flavors_client.list_flavor_extra_specs(
                    self.flavor_ref)['extra_specs']
            if extra_spec_keys:
                self.admin_flavors_client.set_flavor_extra_spec(
                    flavor['id'], **extra_spec_keys)

            return flavor['id']

        flavor_with_eph_disk_id = create_flavor_with_ephemeral(ephem_disk=1)
        flavor_no_eph_disk_id = create_flavor_with_ephemeral(ephem_disk=0)

        admin_pass = self.image_ssh_password

        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        server_no_eph_disk = self.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until='ACTIVE',
            adminPass=admin_pass,
            flavor=flavor_no_eph_disk_id)

        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server_no_eph_disk['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.servers_client.delete_server,
                        server_no_eph_disk['id'])

        # Get partition number of server without ephemeral disk.
        server_no_eph_disk = self.client.show_server(
            server_no_eph_disk['id'])['server']
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(server_no_eph_disk,
                               validation_resources),
            self.ssh_user,
            admin_pass,
            validation_resources['keypair']['private_key'],
            server=server_no_eph_disk,
            servers_client=self.client)
        disks_num = len(linux_client.get_disks().split('\n'))

        # Explicit server deletion necessary for Juno compatibility
        self.client.delete_server(server_no_eph_disk['id'])

        server_with_eph_disk = self.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until='ACTIVE',
            adminPass=admin_pass,
            flavor=flavor_with_eph_disk_id)

        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server_with_eph_disk['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.servers_client.delete_server,
                        server_with_eph_disk['id'])

        server_with_eph_disk = self.client.show_server(
            server_with_eph_disk['id'])['server']
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(server_with_eph_disk,
                               validation_resources),
            self.ssh_user,
            admin_pass,
            validation_resources['keypair']['private_key'],
            server=server_with_eph_disk,
            servers_client=self.client)
        disks_num_eph = len(linux_client.get_disks().split('\n'))
        self.assertEqual(disks_num + 1, disks_num_eph)
