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

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class VolumeMultiBackendTest(base.BaseVolumeV1AdminTest):
    _interface = "json"

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(VolumeMultiBackendTest, cls).setUpClass()
        if not CONF.volume_feature_enabled.multi_backend:
            raise cls.skipException("Cinder multi-backend feature disabled")

        cls.backend1_name = CONF.volume.backend1_name
        cls.backend2_name = CONF.volume.backend2_name

        cls.volume_client = cls.os_adm.volumes_client
        cls.volume_type_id_list = []
        cls.volume_id_list_with_prefix = []
        cls.volume_id_list_without_prefix = []

        # Volume/Type creation (uses volume_backend_name)
        cls._create_type_and_volume(cls.backend1_name, False)
        # Volume/Type creation (uses capabilities:volume_backend_name)
        cls._create_type_and_volume(cls.backend1_name, True)

        if cls.backend1_name != cls.backend2_name:
            # Volume/Type creation (uses backend2_name)
            cls._create_type_and_volume(cls.backend2_name, False)
            # Volume/Type creation (uses capabilities:volume_backend_name)
            cls._create_type_and_volume(cls.backend2_name, True)

    @classmethod
    def _create_type_and_volume(self, backend_name_key, with_prefix):
        # Volume/Type creation
        type_name = data_utils.rand_name('Type')
        vol_name = data_utils.rand_name('Volume')
        spec_key_with_prefix = "capabilities:volume_backend_name"
        spec_key_without_prefix = "volume_backend_name"
        if with_prefix:
            extra_specs = {spec_key_with_prefix: backend_name_key}
        else:
            extra_specs = {spec_key_without_prefix: backend_name_key}
        _, self.type = self.client.create_volume_type(
            type_name, extra_specs=extra_specs)
        self.volume_type_id_list.append(self.type['id'])

        _, self.volume = self.volume_client.create_volume(
            size=1, display_name=vol_name, volume_type=type_name)
        self.volume_client.wait_for_volume_status(
            self.volume['id'], 'available')
        if with_prefix:
            self.volume_id_list_with_prefix.append(self.volume['id'])
        else:
            self.volume_id_list_without_prefix.append(
                self.volume['id'])

    @classmethod
    def tearDownClass(cls):
        # volumes deletion
        vid_prefix = getattr(cls, 'volume_id_list_with_prefix', [])
        for volume_id in vid_prefix:
            cls.volume_client.delete_volume(volume_id)
            cls.volume_client.wait_for_resource_deletion(volume_id)

        vid_no_pre = getattr(cls, 'volume_id_list_without_prefix', [])
        for volume_id in vid_no_pre:
            cls.volume_client.delete_volume(volume_id)
            cls.volume_client.wait_for_resource_deletion(volume_id)

        # volume types deletion
        volume_type_id_list = getattr(cls, 'volume_type_id_list', [])
        for volume_type_id in volume_type_id_list:
            cls.client.delete_volume_type(volume_type_id)

        super(VolumeMultiBackendTest, cls).tearDownClass()

    @test.attr(type='smoke')
    def test_backend_name_reporting(self):
        # get volume id which created by type without prefix
        volume_id = self.volume_id_list_without_prefix[0]
        self._test_backend_name_reporting_by_volume_id(volume_id)

    @test.attr(type='smoke')
    def test_backend_name_reporting_with_prefix(self):
        # get volume id which created by type with prefix
        volume_id = self.volume_id_list_with_prefix[0]
        self._test_backend_name_reporting_by_volume_id(volume_id)

    @test.attr(type='gate')
    def test_backend_name_distinction(self):
        if self.backend1_name == self.backend2_name:
            raise self.skipException("backends configured with same name")
        # get volume id which created by type without prefix
        volume1_id = self.volume_id_list_without_prefix[0]
        volume2_id = self.volume_id_list_without_prefix[1]
        self._test_backend_name_distinction(volume1_id, volume2_id)

    @test.attr(type='gate')
    def test_backend_name_distinction_with_prefix(self):
        if self.backend1_name == self.backend2_name:
            raise self.skipException("backends configured with same name")
        # get volume id which created by type without prefix
        volume1_id = self.volume_id_list_with_prefix[0]
        volume2_id = self.volume_id_list_with_prefix[1]
        self._test_backend_name_distinction(volume1_id, volume2_id)

    def _test_backend_name_reporting_by_volume_id(self, volume_id):
        # this test checks if os-vol-attr:host is populated correctly after
        # the multi backend feature has been enabled
        # if multi-backend is enabled: os-vol-attr:host should be like:
        # host@backend_name
        _, volume = self.volume_client.get_volume(volume_id)

        volume1_host = volume['os-vol-host-attr:host']
        msg = ("multi-backend reporting incorrect values for volume %s" %
               volume_id)
        self.assertTrue(len(volume1_host.split("@")) > 1, msg)

    def _test_backend_name_distinction(self, volume1_id, volume2_id):
        # this test checks that the two volumes created at setUp don't
        # belong to the same backend (if they are, than the
        # volume backend distinction is not working properly)
        _, volume = self.volume_client.get_volume(volume1_id)
        volume1_host = volume['os-vol-host-attr:host']

        _, volume = self.volume_client.get_volume(volume2_id)
        volume2_host = volume['os-vol-host-attr:host']

        msg = ("volumes %s and %s were created in the same backend" %
               (volume1_id, volume2_id))
        self.assertNotEqual(volume1_host, volume2_host, msg)
