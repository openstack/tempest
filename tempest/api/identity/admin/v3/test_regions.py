# Copyright 2014 Hewlett-Packard Development Company, L.P
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

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class RegionsTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(RegionsTestJSON, cls).setUpClass()
        cls.setup_regions = list()
        cls.client = cls.region_client
        for i in range(2):
            r_description = data_utils.rand_name('description-')
            _, region = cls.client.create_region(r_description)
            cls.setup_regions.append(region)

    @classmethod
    def tearDownClass(cls):
        for r in cls.setup_regions:
            cls.client.delete_region(r['id'])
        super(RegionsTestJSON, cls).tearDownClass()

    def _delete_region(self, region_id):
        resp, _ = self.client.delete_region(region_id)
        self.assertEqual(204, resp.status)
        self.assertRaises(exceptions.NotFound,
                          self.client.get_region, region_id)

    @test.attr(type='gate')
    def test_create_update_get_delete_region(self):
        r_description = data_utils.rand_name('description-')
        resp, region = self.client.create_region(
            r_description, parent_region_id=self.setup_regions[0]['id'])
        self.assertEqual(201, resp.status)
        self.addCleanup(self._delete_region, region['id'])
        self.assertEqual(r_description, region['description'])
        self.assertEqual(self.setup_regions[0]['id'],
                         region['parent_region_id'])
        # Update region with new description and parent ID
        r_alt_description = data_utils.rand_name('description-')
        resp, region = self.client.update_region(
            region['id'],
            description=r_alt_description,
            parent_region_id=self.setup_regions[1]['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(r_alt_description, region['description'])
        self.assertEqual(self.setup_regions[1]['id'],
                         region['parent_region_id'])
        # Get the details of region
        resp, region = self.client.get_region(region['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(r_alt_description, region['description'])
        self.assertEqual(self.setup_regions[1]['id'],
                         region['parent_region_id'])

    @test.attr(type='smoke')
    def test_create_region_with_specific_id(self):
        # Create a region with a specific id
        r_region_id = data_utils.rand_uuid()
        r_description = data_utils.rand_name('description-')
        resp, region = self.client.create_region(
            r_description, unique_region_id=r_region_id)
        self.addCleanup(self._delete_region, region['id'])
        # Asserting Create Region with specific id response body
        self.assertEqual(201, resp.status)
        self.assertEqual(r_region_id, region['id'])
        self.assertEqual(r_description, region['description'])

    @test.attr(type='gate')
    def test_list_regions(self):
        # Get a list of regions
        resp, fetched_regions = self.client.list_regions()
        self.assertEqual(200, resp.status)
        missing_regions =\
            [e for e in self.setup_regions if e not in fetched_regions]
        # Asserting List Regions response
        self.assertEqual(0, len(missing_regions),
                         "Failed to find region %s in fetched list" %
                         ', '.join(str(e) for e in missing_regions))


class RegionsTestXML(RegionsTestJSON):
    _interface = 'xml'
