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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ListImageFiltersNegativeTestJSON(base.BaseV2ComputeTest):
    """Negative tests of listing images using compute images API

    Negative tests of listing images using compute images API with
    microversion less than 2.36.
    """

    max_microversion = '2.35'

    @classmethod
    def skip_checks(cls):
        super(ListImageFiltersNegativeTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(ListImageFiltersNegativeTestJSON, cls).setup_clients()
        cls.client = cls.compute_images_client

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('391b0440-432c-4d4b-b5da-c5096aa247eb')
    def test_get_nonexistent_image(self):
        """Test getting a non existent image should fail"""
        nonexistent_image = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.show_image,
                          nonexistent_image)
