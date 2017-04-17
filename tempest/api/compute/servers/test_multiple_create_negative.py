# Copyright 2013 IBM Corp
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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class MultipleCreateNegativeTestJSON(base.BaseV2ComputeTest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('daf29d8d-e928-4a01-9a8c-b129603f3fc0')
    def test_min_count_less_than_one(self):
        invalid_min_count = 0
        self.assertRaises(lib_exc.BadRequest, self.create_test_server,
                          min_count=invalid_min_count)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('999aa722-d624-4423-b813-0d1ac9884d7a')
    def test_min_count_non_integer(self):
        invalid_min_count = 2.5
        self.assertRaises(lib_exc.BadRequest, self.create_test_server,
                          min_count=invalid_min_count)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a6f9c2ab-e060-4b82-b23c-4532cb9390ff')
    def test_max_count_less_than_one(self):
        invalid_max_count = 0
        self.assertRaises(lib_exc.BadRequest, self.create_test_server,
                          max_count=invalid_max_count)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9c5698d1-d7af-4c80-b971-9d403135eea2')
    def test_max_count_non_integer(self):
        invalid_max_count = 2.5
        self.assertRaises(lib_exc.BadRequest, self.create_test_server,
                          max_count=invalid_max_count)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('476da616-f1ef-4271-a9b1-b9fc87727cdf')
    def test_max_count_less_than_min_count(self):
        min_count = 3
        max_count = 2
        self.assertRaises(lib_exc.BadRequest, self.create_test_server,
                          min_count=min_count,
                          max_count=max_count)
