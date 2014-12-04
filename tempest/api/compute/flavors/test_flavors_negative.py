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

from tempest.api.compute import base
from tempest.api_schema.request.compute.v2 import flavors
from tempest import config
from tempest import test


CONF = config.CONF

load_tests = test.NegativeAutoTest.load_tests


@test.SimpleNegativeAutoTest
class FlavorsListWithDetailsNegativeTestJSON(base.BaseV2ComputeTest,
                                             test.NegativeAutoTest):
    _service = CONF.compute.catalog_type
    _schema = flavors.flavor_list


@test.SimpleNegativeAutoTest
class FlavorDetailsNegativeTestJSON(base.BaseV2ComputeTest,
                                    test.NegativeAutoTest):
    _service = CONF.compute.catalog_type
    _schema = flavors.flavors_details

    @classmethod
    def resource_setup(cls):
        super(FlavorDetailsNegativeTestJSON, cls).resource_setup()
        cls.set_resource("flavor", cls.flavor_ref)
