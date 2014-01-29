# Copyright 2014 NEC Corporation.  All rights reserved.
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
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class ListImageFiltersNegativeTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ListImageFiltersNegativeTestJSON, cls).setUpClass()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        cls.client = cls.images_client

    @test.attr(type=['negative', 'gate'])
    def test_get_nonexistent_image(self):
        # Check raises a NotFound
        nonexistent_image = data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound, self.client.get_image,
                          nonexistent_image)


class ListImageFiltersNegativeTestXML(ListImageFiltersNegativeTestJSON):
    _interface = 'xml'
