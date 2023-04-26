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
from tempest import config
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
        server = self.launch_instance()
        volume = self.create_encrypted_volume('luks',
                                              volume_type='luks')
        self.attach_detach_volume(server, volume)

    @decorators.idempotent_id('7abec0a3-61a0-42a5-9e36-ad3138fb38b4')
    @testtools.skipIf(CONF.volume.storage_protocol == 'ceph',
                      'Ceph only supports LUKSv2 if doing host attach.')
    @decorators.attr(type='slow')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_luksv2(self):
        """LUKs v2 decrypts volume through os-brick."""
        server = self.launch_instance()
        volume = self.create_encrypted_volume('luks2',
                                              volume_type='luksv2')
        self.attach_detach_volume(server, volume)

    @decorators.idempotent_id('cbc752ed-b716-4717-910f-956cce965722')
    @decorators.attr(type='slow')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_cryptsetup(self):
        server = self.launch_instance()
        volume = self.create_encrypted_volume('plain',
                                              volume_type='cryptsetup')
        self.attach_detach_volume(server, volume)
