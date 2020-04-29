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
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators


class RegionsTestJSON(base.BaseIdentityV3AdminTest):
    """Test regions"""

    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    @classmethod
    def setup_clients(cls):
        super(RegionsTestJSON, cls).setup_clients()
        cls.client = cls.regions_client

    @classmethod
    def resource_setup(cls):
        super(RegionsTestJSON, cls).resource_setup()
        cls.setup_regions = list()
        for _ in range(2):
            r_description = data_utils.rand_name('description')
            region = cls.client.create_region(
                description=r_description)['region']
            cls.addClassResourceCleanup(
                cls.client.delete_region, region['id'])
            cls.setup_regions.append(region)

    @decorators.idempotent_id('56186092-82e4-43f2-b954-91013218ba42')
    def test_create_update_get_delete_region(self):
        """Test creating, updating, getting and updating region"""
        # Create region
        r_description = data_utils.rand_name('description')
        region = self.client.create_region(
            description=r_description,
            parent_region_id=self.setup_regions[0]['id'])['region']
        # This test will delete the region as part of the validation
        # procedure, so it needs a different cleanup method that
        # would be useful in case the tests fails at any point before
        # reaching the deletion part.
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_region, region['id'])
        self.assertEqual(r_description, region['description'])
        self.assertEqual(self.setup_regions[0]['id'],
                         region['parent_region_id'])
        # Update region with new description and parent ID
        r_alt_description = data_utils.rand_name('description')
        region = self.client.update_region(
            region['id'],
            description=r_alt_description,
            parent_region_id=self.setup_regions[1]['id'])['region']
        self.assertEqual(r_alt_description, region['description'])
        self.assertEqual(self.setup_regions[1]['id'],
                         region['parent_region_id'])
        # Get the details of region
        region = self.client.show_region(region['id'])['region']
        self.assertEqual(r_alt_description, region['description'])
        self.assertEqual(self.setup_regions[1]['id'],
                         region['parent_region_id'])
        # Delete the region
        self.client.delete_region(region['id'])
        body = self.client.list_regions()['regions']
        regions_list = [r['id'] for r in body]
        self.assertNotIn(region['id'], regions_list)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('2c12c5b5-efcf-4aa5-90c5-bff1ab0cdbe2')
    def test_create_region_with_specific_id(self):
        """Test creating region with specific id"""
        r_region_id = data_utils.rand_uuid()
        r_description = data_utils.rand_name('description')
        region = self.client.create_region(
            region_id=r_region_id, description=r_description)['region']
        self.addCleanup(self.client.delete_region, region['id'])
        # Asserting Create Region with specific id response body
        self.assertEqual(r_region_id, region['id'])
        self.assertEqual(r_description, region['description'])

    @decorators.idempotent_id('d180bf99-544a-445c-ad0d-0c0d27663796')
    def test_list_regions(self):
        """Test getting a list of regions"""
        fetched_regions = self.client.list_regions()['regions']
        missing_regions =\
            [e for e in self.setup_regions if e not in fetched_regions]
        # Asserting List Regions response
        self.assertEmpty(missing_regions,
                         "Failed to find region %s in fetched list" %
                         ', '.join(str(e) for e in missing_regions))

    @decorators.idempotent_id('2d1057cb-bbde-413a-acdf-e2d265284542')
    def test_list_regions_filter_by_parent_region_id(self):
        """Test listing regions filtered by parent region id"""
        # Add a sub-region to one of the existing test regions
        r_description = data_utils.rand_name('description')
        region = self.client.create_region(
            description=r_description,
            parent_region_id=self.setup_regions[0]['id'])['region']
        self.addCleanup(self.client.delete_region, region['id'])
        # Get the list of regions filtering with the parent_region_id
        params = {'parent_region_id': self.setup_regions[0]['id']}
        fetched_regions = self.client.list_regions(params=params)['regions']
        # Asserting list regions response
        self.assertIn(region, fetched_regions)
        for r in fetched_regions:
            self.assertEqual(self.setup_regions[0]['id'],
                             r['parent_region_id'])
