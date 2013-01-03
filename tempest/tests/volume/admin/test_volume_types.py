# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from tempest.common.utils.data_utils import rand_name
from tempest.services.volume.json.admin import volume_types_client
from tempest.tests.volume.base import BaseVolumeTest


class VolumeTypesTest(BaseVolumeTest):

    @classmethod
    def setUpClass(cls):
        super(VolumeTypesTest, cls).setUpClass()
        adm_user = cls.config.compute_admin.username
        adm_pass = cls.config.compute_admin.password
        adm_tenant = cls.config.compute_admin.tenant_name
        auth_url = cls.config.identity.auth_url

        cls.client = volume_types_client.VolumeTypesClientJSON(cls.config,
                                                               adm_user,
                                                               adm_pass,
                                                               auth_url,
                                                               adm_tenant)

    @classmethod
    def tearDownClass(cls):
        super(VolumeTypesTest, cls).tearDownClass()

    def test_volume_type_list(self):
        # List Volume types.
        try:
            resp, body = self.client.list_volume_types()
            self.assertEqual(200, resp.status)
            self.assertTrue(type(body), list)
        except Exception:
            self.fail("Could not list volume types")

    def test_create_get_delete_volume_with_volume_type_and_extra_specs(self):
        # Create/get/delete volume with volume_type and extra spec.
        try:
            volume = {}
            vol_name = rand_name("volume-")
            vol_type_name = rand_name("volume-type-")
            extra_specs = {"Spec1": "Val1", "Spec2": "Val2"}
            body = {}
            resp, body = self.client.create_volume_type(vol_type_name,
                                                        extra_specs=
                                                        extra_specs)
            self.assertEqual(200, resp.status)
            self.assertTrue('id' in body)
            self.assertTrue('name' in body)
            resp, volume = self.volumes_client.\
            create_volume(size=1, display_name=vol_name,
                          volume_type=vol_type_name)
            self.assertEqual(200, resp.status)
            self.assertTrue('id' in volume)
            self.assertTrue('display_name' in volume)
            self.assertEqual(volume['display_name'], vol_name,
                             "The created volume name is not equal "
                             "to the requested name")
            self.assertTrue(volume['id'] is not None,
                            "Field volume id is empty or not found.")
            self.volumes_client.wait_for_volume_status(volume['id'],
                                                       'available')
            resp, fetched_volume = self.volumes_client.\
            get_volume(volume['id'])
            self.assertEqual(200, resp.status)
            self.assertEqual(vol_name, fetched_volume['display_name'],
                             'The fetched Volume is different '
                             'from the created Volume')
            self.assertEqual(volume['id'], fetched_volume['id'],
                             'The fetched Volume is different '
                             'from the created Volume')
            self.assertEqual(vol_type_name, fetched_volume['volume_type'],
                             'The fetched Volume is different '
                             'from the created Volume')
        except Exception:
            self.fail("Could not create correct volume with volume_type")
        finally:
            if volume:
                # Delete the Volume if it was created
                resp, _ = self.volumes_client.delete_volume(volume['id'])
                self.assertEqual(202, resp.status)

            if body:
                resp, _ = self.client.delete_volume_type(body['id'])
                self.assertEqual(202, resp.status)

    def test_volume_type_create_delete(self):
        # Create/Delete volume type.
        try:
            name = rand_name("volume-type-")
            extra_specs = {"Spec1": "Val1", "Spec2": "Val2"}
            resp, body = self.client.\
            create_volume_type(name, extra_specs=extra_specs)
            self.assertEqual(200, resp.status)
            self.assertTrue('id' in body)
            self.assertTrue('name' in body)
            self.assertEqual(body['name'], name,
                             "The created volume_type name is not equal "
                             "to the requested name")
            self.assertTrue(body['id'] is not None,
                            "Field volume_type id is empty or not found.")
            resp, fetched_volume_type = self.client.\
            delete_volume_type(body['id'])
            self.assertEqual(202, resp.status)
        except Exception:
            self.fail("Could not create a volume_type")

    def test_volume_type_create_get(self):
        # Create/get volume type.
        try:
            body = {}
            name = rand_name("volume-type-")
            extra_specs = {"Spec1": "Val1", "Spec2": "Val2"}
            resp, body = self.client.\
            create_volume_type(name, extra_specs=extra_specs)
            self.assertEqual(200, resp.status)
            self.assertTrue('id' in body)
            self.assertTrue('name' in body)
            self.assertEqual(body['name'], name,
                             "The created volume_type name is not equal "
                             "to the requested name")
            self.assertTrue(body['id'] is not None,
                            "Field volume_type id is empty or not found.")
            resp, fetched_volume_type = self.client.get_volume_type(body['id'])
            self.assertEqual(200, resp.status)
            self.assertEqual(name, fetched_volume_type['name'],
                             'The fetched Volume_type is different '
                             'from the created Volume_type')
            self.assertEqual(str(body['id']), fetched_volume_type['id'],
                             'The fetched Volume_type is different '
                             'from the created Volume_type')
            self.assertEqual(extra_specs, fetched_volume_type['extra_specs'],
                             'The fetched Volume_type is different '
                             'from the created Volume_type')
        except Exception:
            self.fail("Could not create a volume_type")
        finally:
            if body:
                resp, _ = self.client.delete_volume_type(body['id'])
                self.assertEqual(202, resp.status)
