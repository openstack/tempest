# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest.test import attr
from testtools.matchers import ContainsAll


class VolumesGetTestJSON(base.BaseV2ComputeTest):

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(VolumesGetTestJSON, cls).setUpClass()
        cls.client = cls.volumes_extensions_client
        if not cls.config.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @attr(type='smoke')
    def test_volume_create_get_delete(self):
        # CREATE, GET, DELETE Volume
        volume = None
        v_name = data_utils.rand_name('Volume-%s-') % self._interface
        metadata = {'Type': 'work'}
        # Create volume
        resp, volume = self.client.create_volume(size=1,
                                                 display_name=v_name,
                                                 metadata=metadata)
        self.addCleanup(self._delete_volume, volume)
        self.assertEqual(200, resp.status)
        self.assertIn('id', volume)
        self.assertIn('displayName', volume)
        self.assertEqual(volume['displayName'], v_name,
                         "The created volume name is not equal "
                         "to the requested name")
        self.assertTrue(volume['id'] is not None,
                        "Field volume id is empty or not found.")
        # Wait for Volume status to become ACTIVE
        self.client.wait_for_volume_status(volume['id'], 'available')
        # GET Volume
        resp, fetched_volume = self.client.get_volume(volume['id'])
        self.assertEqual(200, resp.status)
        # Verfication of details of fetched Volume
        self.assertEqual(v_name,
                         fetched_volume['displayName'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertEqual(volume['id'],
                         fetched_volume['id'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertThat(fetched_volume['metadata'].items(),
                        ContainsAll(metadata.items()),
                        'The fetched Volume metadata misses data '
                        'from the created Volume')

    def _delete_volume(self, volume):
        # Delete the Volume created in this method
        try:
            resp, _ = self.client.delete_volume(volume['id'])
            self.assertEqual(202, resp.status)
            # Checking if the deleted Volume still exists
            self.client.wait_for_resource_deletion(volume['id'])
        except KeyError:
            return


class VolumesGetTestXML(VolumesGetTestJSON):
    _interface = "xml"
