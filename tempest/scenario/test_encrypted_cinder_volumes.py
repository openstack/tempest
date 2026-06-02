# Copyright (c) 2014 The Johns Hopkins University/Applied Physics Laboratory
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

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF


class TestEncryptedCinderVolumes(manager.EncryptionScenarioTest):

    """The test suite for encrypted cinder volumes

    This test is for verifying the functionality of encrypted cinder volumes.

    For both LUKS (v1 & v2) and cryptsetup encryption types, this test performs
    the following:

    * Boots an instance from an image (CONF.compute.image_ref)
    * Creates an encryption type (as admin)
    * Creates a volume of that encryption type (as a regular user)
    * Attaches and detaches the encrypted volume to the instance
    """

    @classmethod
    def skip_checks(cls):
        super(TestEncryptedCinderVolumes, cls).skip_checks()
        if not CONF.compute_feature_enabled.attach_encrypted_volume:
            raise cls.skipException('Encrypted volume attach is not supported')

    def launch_instance(self):
        return self.create_server(wait_until='SSHABLE')

    def attach_detach_volume(self, server, volume):
        attached_volume = self.nova_volume_attach(server, volume)
        self.nova_volume_detach(server, attached_volume)

    @decorators.idempotent_id('79165fb4-5534-4b9d-8429-97ccffb8f86e')
    @decorators.attr(type='slow')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_luks(self):
        """LUKs v1 decrypts volume through libvirt."""
        volume = self.create_encrypted_volume('luks',
                                              volume_type='luks',
                                              wait_until=None)
        server = self.launch_instance()
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        # The volume retrieved on creation has a non-up-to-date status.
        # Retrieval after it becomes active ensures correct details.
        volume = self.volumes_client.show_volume(volume['id'])['volume']

        self.attach_detach_volume(server, volume)

    @decorators.idempotent_id('7abec0a3-61a0-42a5-9e36-ad3138fb38b4')
    @testtools.skipIf(CONF.volume.storage_protocol == 'ceph',
                      'Ceph only supports LUKSv2 if doing host attach.')
    @decorators.attr(type='slow')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_luksv2(self):
        """LUKs v2 decrypts volume through os-brick."""
        volume = self.create_encrypted_volume('luks2',
                                              volume_type='luksv2',
                                              wait_until=None)
        server = self.launch_instance()
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        # The volume retrieved on creation has a non-up-to-date status.
        # Retrieval after it becomes active ensures correct details.
        volume = self.volumes_client.show_volume(volume['id'])['volume']

        self.attach_detach_volume(server, volume)

    @decorators.idempotent_id('cbc752ed-b716-4717-910f-956cce965722')
    @decorators.attr(type='slow')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_cryptsetup(self):
        volume = self.create_encrypted_volume('plain',
                                              volume_type='cryptsetup',
                                              wait_until=None)
        server = self.launch_instance()
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        # The volume retrieved on creation has a non-up-to-date status.
        # Retrieval after it becomes active ensures correct details.
        volume = self.volumes_client.show_volume(volume['id'])['volume']

        self.attach_detach_volume(server, volume)

    @decorators.idempotent_id('d653af24-fa18-470d-b9bf-af287cefeba9')
    @decorators.attr(type='slow')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_resize_revert(self):
        """Test resize revert for a server with an attached encrypted volume.

        During a resize revert, some cleanup occurs when moving the server back
        from the destination compute host to the source compute host. This test
        sanity checks that things work normally after that cleanup happens,
        especially with regard to the key manager secrets.

        Steps:

        1. Create a LUKS encrypted volume
        2. Create a server and attach the encrypted volume
        3. Resize the server while the volume is attached
        4. Revert the resize while the volume is attached
        5. Detach the encrypted volume
        """
        volume = self.create_encrypted_volume('luks',
                                              volume_type='luks',
                                              wait_until=None)
        server = self.launch_instance()
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        # The volume retrieved on creation has a non-up-to-date status.
        # Retrieval after it becomes active ensures correct details.
        volume = self.volumes_client.show_volume(volume['id'])['volume']

        attached_volume = self.nova_volume_attach(server, volume)

        # Create a new flavor based on the default -- we just want to take the
        # resize code path.
        default_flavor = self.flavors_client.show_flavor(
            CONF.compute.flavor_ref)['flavor']
        flavor_name = data_utils.rand_name(prefix=CONF.resource_name_prefix)
        new_flavor = self.os_admin.flavors_client.create_flavor(
            name=flavor_name, vcpus=default_flavor['vcpus'],
            ram=default_flavor['ram'], disk=default_flavor['disk'])['flavor']

        # Resize the server to VERIFY_RESIZE state.
        body = self.servers_client.resize_server(
            server['id'], new_flavor['id'])
        waiters.wait_for_server_status(
            self.servers_client, server['id'], 'VERIFY_RESIZE',
            request_id=body.response['x-openstack-request-id'])

        # Revert the resize and expect the server to return to ACTIVE state.
        self.servers_client.revert_resize_server(server['id'])
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')

        # Wait for volume status to be "in-use" as well -- this may not
        # necessarily be the case yet at the time the server returns to ACTIVE.
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'in-use')
        self.nova_volume_detach(server, attached_volume)
