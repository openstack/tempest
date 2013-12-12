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

import uuid

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class FlavorsNegativeTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FlavorsNegativeTestJSON, cls).setUpClass()
        cls.client = cls.flavors_client

        # Generating a nonexistent flavor id
        resp, flavors = cls.client.list_flavors()
        flavor_ids = [flavor['id'] for flavor in flavors]
        while True:
            cls.nonexistent_flavor_id = data_utils.rand_int_id(start=999)
            if cls.nonexistent_flavor_id not in flavor_ids:
                break

    @attr(type=['negative', 'gate'])
    def test_invalid_minRam_filter(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.list_flavors_with_detail,
                          {'minRam': 'invalid'})

    @attr(type=['negative', 'gate'])
    def test_invalid_minDisk_filter(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.list_flavors_with_detail,
                          {'minDisk': 'invalid'})

    @attr(type=['negative', 'gate'])
    def test_get_flavor_details_for_invalid_flavor_id(self):
        # Ensure 404 returned for invalid flavor ID
        invalid_flavor_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound, self.client.get_flavor_details,
                          invalid_flavor_id)

    @attr(type=['negative', 'gate'])
    def test_non_existent_flavor_id(self):
        # flavor details are not returned for non-existent flavors
        self.assertRaises(exceptions.NotFound, self.client.get_flavor_details,
                          self.nonexistent_flavor_id)


class FlavorsNegativeTestXML(FlavorsNegativeTestJSON):
    _interface = 'xml'
