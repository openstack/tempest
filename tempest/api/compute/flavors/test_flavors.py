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
from tempest import test


class FlavorsV2TestJSON(base.BaseComputeTest):

    _api_version = 2
    _min_disk = 'minDisk'
    _min_ram = 'minRam'

    @classmethod
    def setup_clients(cls):
        super(FlavorsV2TestJSON, cls).setup_clients()
        cls.client = cls.flavors_client

    @test.attr(type='smoke')
    @test.idempotent_id('e36c0eaa-dff5-4082-ad1f-3f9a80aa3f59')
    def test_list_flavors(self):
        # List of all flavors should contain the expected flavor
        flavors = self.client.list_flavors()
        flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_min_detail = {'id': flavor['id'], 'links': flavor['links'],
                             'name': flavor['name']}
        self.assertIn(flavor_min_detail, flavors)

    @test.attr(type='smoke')
    @test.idempotent_id('6e85fde4-b3cd-4137-ab72-ed5f418e8c24')
    def test_list_flavors_with_detail(self):
        # Detailed list of all flavors should contain the expected flavor
        flavors = self.client.list_flavors_with_detail()
        flavor = self.client.get_flavor_details(self.flavor_ref)
        self.assertIn(flavor, flavors)

    @test.attr(type='smoke')
    @test.idempotent_id('1f12046b-753d-40d2-abb6-d8eb8b30cb2f')
    def test_get_flavor(self):
        # The expected flavor details should be returned
        flavor = self.client.get_flavor_details(self.flavor_ref)
        self.assertEqual(self.flavor_ref, flavor['id'])

    @test.attr(type='gate')
    @test.idempotent_id('8d7691b3-6ed4-411a-abc9-2839a765adab')
    def test_list_flavors_limit_results(self):
        # Only the expected number of flavors should be returned
        params = {'limit': 1}
        flavors = self.client.list_flavors(params)
        self.assertEqual(1, len(flavors))

    @test.attr(type='gate')
    @test.idempotent_id('b26f6327-2886-467a-82be-cef7a27709cb')
    def test_list_flavors_detailed_limit_results(self):
        # Only the expected number of flavors (detailed) should be returned
        params = {'limit': 1}
        flavors = self.client.list_flavors_with_detail(params)
        self.assertEqual(1, len(flavors))

    @test.attr(type='gate')
    @test.idempotent_id('e800f879-9828-4bd0-8eae-4f17189951fb')
    def test_list_flavors_using_marker(self):
        # The list of flavors should start from the provided marker
        flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_id = flavor['id']

        params = {'marker': flavor_id}
        flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]),
                         'The list of flavors did not start after the marker.')

    @test.attr(type='gate')
    @test.idempotent_id('6db2f0c0-ddee-4162-9c84-0703d3dd1107')
    def test_list_flavors_detailed_using_marker(self):
        # The list of flavors should start from the provided marker
        flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_id = flavor['id']

        params = {'marker': flavor_id}
        flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]),
                         'The list of flavors did not start after the marker.')

    @test.attr(type='gate')
    @test.idempotent_id('3df2743e-3034-4e57-a4cb-b6527f6eac79')
    def test_list_flavors_detailed_filter_by_min_disk(self):
        # The detailed list of flavors should be filtered by disk space
        flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_id = flavor['id']

        params = {self._min_disk: flavor['disk'] + 1}
        flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @test.attr(type='gate')
    @test.idempotent_id('09fe7509-b4ee-4b34-bf8b-39532dc47292')
    def test_list_flavors_detailed_filter_by_min_ram(self):
        # The detailed list of flavors should be filtered by RAM
        flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_id = flavor['id']

        params = {self._min_ram: flavor['ram'] + 1}
        flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @test.attr(type='gate')
    @test.idempotent_id('10645a4d-96f5-443f-831b-730711e11dd4')
    def test_list_flavors_filter_by_min_disk(self):
        # The list of flavors should be filtered by disk space
        flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_id = flavor['id']

        params = {self._min_disk: flavor['disk'] + 1}
        flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @test.attr(type='gate')
    @test.idempotent_id('935cf550-e7c8-4da6-8002-00f92d5edfaa')
    def test_list_flavors_filter_by_min_ram(self):
        # The list of flavors should be filtered by RAM
        flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_id = flavor['id']

        params = {self._min_ram: flavor['ram'] + 1}
        flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))
