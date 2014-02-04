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
from tempest import exceptions
from tempest.test import attr


class FlavorsNegativeTestXML(base.BaseV2ComputeTest):
    _interface = 'xml'

    @classmethod
    def setUpClass(cls):
        super(FlavorsNegativeTestXML, cls).setUpClass()
        cls.client = cls.flavors_client

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
    def test_non_existent_flavor_id(self):
        # flavor details are not returned for non-existent flavors
        nonexistent_flavor_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound, self.client.get_flavor_details,
                          nonexistent_flavor_id)
