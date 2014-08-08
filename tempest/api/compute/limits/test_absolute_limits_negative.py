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
from tempest import exceptions
from tempest import test


class AbsoluteLimitsNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setUpClass(cls):
        super(AbsoluteLimitsNegativeTestJSON, cls).setUpClass()
        cls.client = cls.limits_client
        cls.server_client = cls.servers_client

    @test.attr(type=['negative', 'gate'])
    def test_max_image_meta_exceed_limit(self):
        # We should not create vm with image meta over maxImageMeta limit
        # Get max limit value
        max_meta = self.client.get_specific_absolute_limit('maxImageMeta')

        # Create server should fail, since we are passing > metadata Limit!
        max_meta_data = int(max_meta) + 1

        meta_data = {}
        for xx in range(max_meta_data):
            meta_data[str(xx)] = str(xx)

        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((exceptions.Unauthorized, exceptions.OverLimit),
                          self.server_client.create_server,
                          name='test', meta=meta_data,
                          flavor_ref=self.flavor_ref,
                          image_ref=self.image_ref)


class AbsoluteLimitsNegativeTestXML(AbsoluteLimitsNegativeTestJSON):
    _interface = 'xml'
