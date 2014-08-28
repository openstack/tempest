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

import uuid

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF

class VolumesBackupsNegativeTest(base.BaseVolumeV1AdminTest):
    _interface = "json"

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(VolumesBackupsNegativeTest, cls).setUpClass()

        if not CONF.volume_feature_enabled.backup:
            raise cls.skipException("Cinder backup feature disabled")

        if cls._api_version == 1:
            cls.volumes_adm_client = cls.os_adm.volumes_client
            cls.backups_adm_client = cls.os_adm.backups_client
        elif cls._api_version == 2:
            cls.volumes_adm_client = cls.os_adm.volumes_v2_client
            cls.backups_adm_client = cls.os_adm.backups_v2_client

        cls.volume = cls.create_volume()

    @classmethod
    def tearDownClass(cls):
        super(VolumesBackupsNegativeTest, cls).tearDownClass()

    @test.attr(type=['negative', 'gate'])
    def test_create_volume_backup_with_nonexistent_volume_id(self):
        # Create a volume backup with nonexistent volume id
        backup_name = data_utils.rand_name('Backup')
        self.assertRaises(exceptions.NotFound,
                          self.backups_adm_client.create_backup,
                          str(uuid.uuid4()), name=backup_name)


    @test.attr(type=['negative', 'gate'])
    def test_get_volume_backup_with_nonexistent_backup_id(self):
        # Should not be able to get volume backup with nonexistent backup id.
        self.assertRaises(exceptions.NotFound,
                         self.backups_adm_client.get_backup,
                         str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    def test_delete_volume_backup_with_nonexistent_backup_id(self):
        # Should not be able to delete volume backup with nonexistent backup id.
        self.assertRaises(exceptions.NotFound,
                          self.backups_adm_client.delete_backup,
                          str(uuid.uuid4()))


    @test.attr(type=['negative', 'gate'])
    def test_restore_volume_backup_with_nonexistent_backup_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.backups_adm_client.restore_backup,
                          str(uuid.uuid4()))

class VolumesBackupsV2NegativeTest(VolumesBackupsNegativeTest):
    _api_version= 2

