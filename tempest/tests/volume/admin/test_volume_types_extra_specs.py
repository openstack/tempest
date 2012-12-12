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


class VolumeTypesExtraSpecsTest(BaseVolumeTest):

    @classmethod
    def setUpClass(cls):
        super(VolumeTypesExtraSpecsTest, cls).setUpClass()

        adm_user = cls.config.compute_admin.username
        adm_pass = cls.config.compute_admin.password
        adm_tenant = cls.config.compute_admin.tenant_name
        auth_url = cls.config.identity.auth_url

        cls.client = volume_types_client.VolumeTypesClientJSON(cls.config,
                                                               adm_user,
                                                               adm_pass,
                                                               auth_url,
                                                               adm_tenant)

        vol_type_name = rand_name('Volume-type-')
        cls.extra_spec = {"spec1": "val1"}
        resp, cls.volume_type = cls.client.create_volume_type(vol_type_name)

    @classmethod
    def tearDownClass(cls):
        super(VolumeTypesExtraSpecsTest, cls).tearDownClass()
        cls.client.delete_volume_type(cls.volume_type['id'])

    def test_volume_type_extra_specs_list(self):
        """List Volume types extra specs."""
        try:
            resp, body = self.client.\
            list_volume_types_extra_specs(self.volume_type['id'])
            self.assertEqual(200, resp.status)
            self.assertTrue(type(body), dict)
            self.assertTrue('spec1' in body, "Incorrect volume type extra"
                            " spec returned")
        except Exception:
            self.fail("Could not list volume types extra specs")

    def test_volume_type_extra_specs_update(self):
        """ Update volume type extra specs"""
        try:
            extra_spec = {"spec1": "val2"}
            resp, body = self.client.\
            update_volume_type_extra_specs(self.volume_type['id'],
                                           extra_spec.keys()[0],
                                           extra_spec)
            self.assertEqual(200, resp.status)
            self.assertTrue('spec1' in body,
                            "Volume type extra spec incorrectly updated")
            self.assertEqual(extra_spec['spec1'], body['spec1'],
                             "Volume type extra spec incorrectly updated")
        except Exception:
            self.fail("Couldnt update volume type extra spec")

    def test_volume_type_extra_spec_create_delete(self):
        """ Create/Delete volume type extra spec."""
        try:
            extra_specs = {"spec2": "val1"}
            resp, body = self.client.\
            create_volume_type_extra_specs(self.volume_type['id'], extra_specs)
            self.assertEqual(200, resp.status)
            self.assertEqual(extra_specs, body,
                             "Volume type extra spec incorrectly created")
            resp, _ = self.client.\
            delete_volume_type_extra_specs(self.volume_type['id'],
                                           extra_specs.keys()[0])
            self.assertEqual(202, resp.status)
        except Exception:
            self.fail("Could not create a volume_type extra spec")

    def test_volume_type_extra_spec_create_get(self):
        """ Create/get volume type extra spec"""
        try:
            extra_specs = {"spec1": "val1"}
            resp, body = self.client.\
            create_volume_type_extra_specs(self.volume_type['id'], extra_specs)
            self.assertEqual(200, resp.status)
            self.assertEqual(extra_specs, body,
                             "Volume type extra spec incorrectly created")
            resp, fetched_vol_type_extra_spec = self.client.\
            get_volume_type_extra_specs(self.volume_type['id'],
                                        extra_specs.keys()[0])
            self.assertEqual(200, resp.status)
            self.assertEqual(extra_specs, body,
                             "Volume type extra spec incorrectly fetched")
        except Exception:
            self.fail("Could not create a volume_type extra spec")
