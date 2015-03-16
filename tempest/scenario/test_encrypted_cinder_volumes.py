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

from tempest.scenario import manager
from tempest import test


class TestEncryptedCinderVolumes(manager.EncryptionScenarioTest):

    """
    This test is for verifying the functionality of encrypted cinder volumes.

    For both LUKS and cryptsetup encryption types, this test performs
    the following:
        * Creates an image in Glance
        * Boots an instance from the image
        * Creates an encryption type (as admin)
        * Creates a volume of that encryption type (as a regular user)
        * Attaches and detaches the encrypted volume to the instance
    """

    def launch_instance(self):
        self.glance_image_create()
        self.nova_boot()

    def create_encrypted_volume(self, encryption_provider, volume_type):
        volume_type = self.create_volume_type(name=volume_type)
        self.create_encryption_type(type_id=volume_type['id'],
                                    provider=encryption_provider,
                                    key_size=512,
                                    cipher='aes-xts-plain64',
                                    control_location='front-end')
        self.volume = self.create_volume(volume_type=volume_type['name'])

    def attach_detach_volume(self):
        self.nova_volume_attach()
        self.nova_volume_detach()

    @test.idempotent_id('79165fb4-5534-4b9d-8429-97ccffb8f86e')
    @test.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_luks(self):
        self.launch_instance()
        self.create_encrypted_volume('nova.volume.encryptors.'
                                     'luks.LuksEncryptor',
                                     volume_type='luks')
        self.attach_detach_volume()

    @test.idempotent_id('cbc752ed-b716-4717-910f-956cce965722')
    @test.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_cryptsetup(self):
        self.launch_instance()
        self.create_encrypted_volume('nova.volume.encryptors.'
                                     'cryptsetup.CryptsetupEncryptor',
                                     volume_type='cryptsetup')
        self.attach_detach_volume()
