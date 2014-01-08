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
from tempest.test import attr


class FlavorsTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FlavorsTestJSON, cls).setUpClass()
        cls.client = cls.flavors_client

    @attr(type='smoke')
    def test_list_flavors(self):
        # List of all flavors should contain the expected flavor
        resp, flavors = self.client.list_flavors()
        resp, flavor = self.client.get_flavor_details(self.flavor_ref)
        flavor_min_detail = {'id': flavor['id'], 'links': flavor['links'],
                             'name': flavor['name']}
        self.assertIn(flavor_min_detail, flavors)

    @attr(type='smoke')
    def test_list_flavors_with_detail(self):
        # Detailed list of all flavors should contain the expected flavor
        resp, flavors = self.client.list_flavors_with_detail()
        resp, flavor = self.client.get_flavor_details(self.flavor_ref)
        self.assertIn(flavor, flavors)

    @attr(type='smoke')
    def test_get_flavor(self):
        # The expected flavor details should be returned
        resp, flavor = self.client.get_flavor_details(self.flavor_ref)
        self.assertEqual(self.flavor_ref, flavor['id'])

    @attr(type='gate')
    def test_list_flavors_limit_results(self):
        # Only the expected number of flavors should be returned
        params = {'limit': 1}
        resp, flavors = self.client.list_flavors(params)
        self.assertEqual(1, len(flavors))

    @attr(type='gate')
    def test_list_flavors_detailed_limit_results(self):
        # Only the expected number of flavors (detailed) should be returned
        params = {'limit': 1}
        resp, flavors = self.client.list_flavors_with_detail(params)
        self.assertEqual(1, len(flavors))

    @attr(type='gate')
    def test_list_flavors_using_marker(self):
        # The list of flavors should start from the provided marker
        resp, flavors = self.client.list_flavors()
        flavor_id = flavors[0]['id']

        params = {'marker': flavor_id}
        resp, flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]),
                         'The list of flavors did not start after the marker.')

    @attr(type='gate')
    def test_list_flavors_detailed_using_marker(self):
        # The list of flavors should start from the provided marker
        resp, flavors = self.client.list_flavors_with_detail()
        flavor_id = flavors[0]['id']

        params = {'marker': flavor_id}
        resp, flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]),
                         'The list of flavors did not start after the marker.')

    @attr(type='gate')
    def test_list_flavors_detailed_filter_by_min_disk(self):
        # The detailed list of flavors should be filtered by disk space
        resp, flavors = self.client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['disk'])
        flavor_id = flavors[0]['id']

        params = {'minDisk': flavors[0]['disk'] + 1}
        resp, flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @attr(type='gate')
    def test_list_flavors_detailed_filter_by_min_ram(self):
        # The detailed list of flavors should be filtered by RAM
        resp, flavors = self.client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['ram'])
        flavor_id = flavors[0]['id']

        params = {'minRam': flavors[0]['ram'] + 1}
        resp, flavors = self.client.list_flavors_with_detail(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @attr(type='gate')
    def test_list_flavors_filter_by_min_disk(self):
        # The list of flavors should be filtered by disk space
        resp, flavors = self.client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['disk'])
        flavor_id = flavors[0]['id']

        params = {'minDisk': flavors[0]['disk'] + 1}
        resp, flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))

    @attr(type='gate')
    def test_list_flavors_filter_by_min_ram(self):
        # The list of flavors should be filtered by RAM
        resp, flavors = self.client.list_flavors_with_detail()
        flavors = sorted(flavors, key=lambda k: k['ram'])
        flavor_id = flavors[0]['id']

        params = {'minRam': flavors[0]['ram'] + 1}
        resp, flavors = self.client.list_flavors(params)
        self.assertFalse(any([i for i in flavors if i['id'] == flavor_id]))


class FlavorsTestXML(FlavorsTestJSON):
    _interface = 'xml'
