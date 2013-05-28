# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
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

from tempest.api.volume import base
from tempest.common import log as logging
from tempest.common.utils.data_utils import rand_name
from tempest import config
from tempest.services.volume.json.admin import volume_types_client
from tempest.services.volume.json import volumes_client
from tempest.test import attr

LOG = logging.getLogger(__name__)


class VolumeMultiBackendTest(base.BaseVolumeAdminTest):
    _interface = "json"

    multi_backend_enabled = config.TempestConfig().volume.multi_backend_enabled
    backend1_name = config.TempestConfig().volume.backend1_name
    backend2_name = config.TempestConfig().volume.backend2_name
    backend_names_equal = False
    if (backend1_name == backend2_name):
        backend_names_equal = True

    @classmethod
    @testtools.skipIf(not multi_backend_enabled,
                      "Cinder multi-backend feature is not available")
    def setUpClass(cls):
        super(VolumeMultiBackendTest, cls).setUpClass()

        adm_user = cls.config.identity.admin_username
        adm_pass = cls.config.identity.admin_password
        adm_tenant = cls.config.identity.admin_tenant_name
        auth_url = cls.config.identity.uri

        cls.client = volumes_client.VolumesClientJSON(cls.config,
                                                      adm_user,
                                                      adm_pass,
                                                      auth_url,
                                                      adm_tenant)
        cls.client2 = volume_types_client.VolumeTypesClientJSON(cls.config,
                                                                adm_user,
                                                                adm_pass,
                                                                auth_url,
                                                                adm_tenant)

        ## variables initialization
        type_name1 = rand_name('type-')
        type_name2 = rand_name('type-')
        cls.volume_type_list = []

        vol_name1 = rand_name('Volume-')
        vol_name2 = rand_name('Volume-')
        cls.volume_id_list = []

        try:
            ## Volume types creation
            extra_specs1 = {"volume_backend_name": cls.backend1_name}
            resp, cls.body1 = cls.client2.create_volume_type(
                type_name1, extra_specs=extra_specs1)
            cls.volume_type_list.append(cls.body1)

            extra_specs2 = {"volume_backend_name": cls.backend2_name}
            resp, cls.body2 = cls.client2.create_volume_type(
                type_name2, extra_specs=extra_specs2)
            cls.volume_type_list.append(cls.body2)

            ## Volumes creation
            resp, cls.volume1 = cls.client.create_volume(
                size=1, display_name=vol_name1, volume_type=type_name1)
            cls.client.wait_for_volume_status(cls.volume1['id'], 'available')
            cls.volume_id_list.append(cls.volume1['id'])

            resp, cls.volume2 = cls.client.create_volume(
                size=1, display_name=vol_name2, volume_type=type_name2)
            cls.client.wait_for_volume_status(cls.volume2['id'], 'available')
            cls.volume_id_list.append(cls.volume2['id'])
        except Exception:
            LOG.exception("setup failed")
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        ## volumes deletion
        for volume_id in cls.volume_id_list:
            cls.client.delete_volume(volume_id)
            cls.client.wait_for_resource_deletion(volume_id)

        ## volume types deletion
        for volume_type in cls.volume_type_list:
            cls.client2.delete_volume_type(volume_type)

        super(VolumeMultiBackendTest, cls).tearDownClass()

    @attr(type='smoke')
    def test_multi_backend_enabled(self):
        # this test checks that multi backend is enabled for at least the
        # computes where the volumes created in setUp were made
        # if multi-backend is enabled: os-vol-attr:host should be like:
        # host@backend_name
        # this test fails if:
        # - multi backend is not enabled
        resp, fetched_volume = self.client.get_volume(self.volume1['id'])
        self.assertEqual(200, resp.status)

        volume_host1 = fetched_volume['os-vol-host-attr:host']
        msg = ("Multi-backend is not available for at least host "
               "%(volume_host1)s") % locals()
        self.assertTrue(len(volume_host1.split("@")) > 1, msg)

        resp, fetched_volume = self.client.get_volume(self.volume2['id'])
        self.assertEqual(200, resp.status)

        volume_host2 = fetched_volume['os-vol-host-attr:host']
        msg = ("Multi-backend is not available for at least host "
               "%(volume_host2)s") % locals()
        self.assertTrue(len(volume_host2.split("@")) > 1, msg)

    @attr(type='gate')
    def test_backend_name_distinction(self):
        # this test checks that the two volumes created at setUp doesn't
        # belong to the same backend (if they are in the same backend, that
        # means, volume_backend_name distinction is not working properly)
        # this test fails if:
        # - tempest.conf is not well configured
        # - the two volumes belongs to the same backend

        # checks tempest.conf
        msg = ("tempest.conf is not well configured, "
               "backend1_name and backend2_name are equal")
        self.assertEqual(self.backend_names_equal, False, msg)

        # checks the two volumes belongs to different backend
        resp, fetched_volume = self.client.get_volume(self.volume1['id'])
        volume_host1 = fetched_volume['os-vol-host-attr:host']

        resp, fetched_volume = self.client.get_volume(self.volume2['id'])
        volume_host2 = fetched_volume['os-vol-host-attr:host']

        msg = ("volume2 was created in the same backend as volume1: "
               "%(volume_host2)s.") % locals()
        self.assertNotEqual(volume_host2, volume_host1, msg)
