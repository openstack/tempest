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
from tempest.openstack.common import log as logging
from tempest.services.volume.json.admin import volume_types_client
from tempest.services.volume.json import volumes_client
from tempest.test import attr

LOG = logging.getLogger(__name__)


class VolumeMultiBackendTest(base.BaseVolumeV1AdminTest):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(VolumeMultiBackendTest, cls).setUpClass()
        if not cls.config.volume_feature_enabled.multi_backend:
            cls.tearDownClass()
            raise cls.skipException("Cinder multi-backend feature disabled")

        cls.backend1_name = cls.config.volume.backend1_name
        cls.backend2_name = cls.config.volume.backend2_name

        adm_user = cls.config.identity.admin_username
        adm_pass = cls.config.identity.admin_password
        adm_tenant = cls.config.identity.admin_tenant_name
        auth_url = cls.config.identity.uri

        cls.volume_client = volumes_client.VolumesClientJSON(cls.config,
                                                             adm_user,
                                                             adm_pass,
                                                             auth_url,
                                                             adm_tenant)
        cls.type_client = volume_types_client.VolumeTypesClientJSON(cls.config,
                                                                    adm_user,
                                                                    adm_pass,
                                                                    auth_url,
                                                                    adm_tenant)

        cls.volume_type_id_list = []
        cls.volume_id_list = []
        try:
            # Volume/Type creation (uses backend1_name)
            type1_name = data_utils.rand_name('Type-')
            vol1_name = data_utils.rand_name('Volume-')
            extra_specs1 = {"volume_backend_name": cls.backend1_name}
            resp, cls.type1 = cls.type_client.create_volume_type(
                type1_name, extra_specs=extra_specs1)
            cls.volume_type_id_list.append(cls.type1['id'])

            resp, cls.volume1 = cls.volume_client.create_volume(
                size=1, display_name=vol1_name, volume_type=type1_name)
            cls.volume_id_list.append(cls.volume1['id'])
            cls.volume_client.wait_for_volume_status(cls.volume1['id'],
                                                     'available')

            if cls.backend1_name != cls.backend2_name:
                # Volume/Type creation (uses backend2_name)
                type2_name = data_utils.rand_name('Type-')
                vol2_name = data_utils.rand_name('Volume-')
                extra_specs2 = {"volume_backend_name": cls.backend2_name}
                resp, cls.type2 = cls.type_client.create_volume_type(
                    type2_name, extra_specs=extra_specs2)
                cls.volume_type_id_list.append(cls.type2['id'])

                resp, cls.volume2 = cls.volume_client.create_volume(
                    size=1, display_name=vol2_name, volume_type=type2_name)
                cls.volume_id_list.append(cls.volume2['id'])
                cls.volume_client.wait_for_volume_status(cls.volume2['id'],
                                                         'available')
        except Exception as e:
            LOG.exception("setup failed: %s" % e)
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        # volumes deletion
        volume_id_list = getattr(cls, 'volume_id_list', [])
        for volume_id in volume_id_list:
            cls.volume_client.delete_volume(volume_id)
            cls.volume_client.wait_for_resource_deletion(volume_id)

        # volume types deletion
        volume_type_id_list = getattr(cls, 'volume_type_id_list', [])
        for volume_type_id in volume_type_id_list:
            cls.type_client.delete_volume_type(volume_type_id)

        super(VolumeMultiBackendTest, cls).tearDownClass()

    @attr(type='smoke')
    def test_backend_name_reporting(self):
        # this test checks if os-vol-attr:host is populated correctly after
        # the multi backend feature has been enabled
        # if multi-backend is enabled: os-vol-attr:host should be like:
        # host@backend_name
        resp, volume = self.volume_client.get_volume(self.volume1['id'])
        self.assertEqual(200, resp.status)

        volume1_host = volume['os-vol-host-attr:host']
        msg = ("multi-backend reporting incorrect values for volume %s" %
               self.volume1['id'])
        self.assertTrue(len(volume1_host.split("@")) > 1, msg)

    @attr(type='gate')
    def test_backend_name_distinction(self):
        # this test checks that the two volumes created at setUp don't
        # belong to the same backend (if they are, than the
        # volume backend distinction is not working properly)
        if self.backend1_name == self.backend2_name:
            raise self.skipException("backends configured with same name")

        resp, volume = self.volume_client.get_volume(self.volume1['id'])
        volume1_host = volume['os-vol-host-attr:host']

        resp, volume = self.volume_client.get_volume(self.volume2['id'])
        volume2_host = volume['os-vol-host-attr:host']

        msg = ("volumes %s and %s were created in the same backend" %
               (self.volume1['id'], self.volume2['id']))
        self.assertNotEqual(volume1_host, volume2_host, msg)
