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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class MultipleCreateNegativeTestJSON(base.BaseV2ComputeTest):
    _name = 'multiple-create-test'

    def _generate_name(self):
        return data_utils.rand_name(self._name)

    def _create_multiple_servers(self, name=None, wait_until=None, **kwargs):
        """
        This is the right way to create_multiple servers and manage to get the
        created servers into the servers list to be cleaned up after all.
        """
        kwargs['name'] = kwargs.get('name', self._generate_name())
        body = self.create_test_server(**kwargs)

        return body

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('daf29d8d-e928-4a01-9a8c-b129603f3fc0')
    def test_min_count_less_than_one(self):
        invalid_min_count = 0
        self.assertRaises(lib_exc.BadRequest, self._create_multiple_servers,
                          min_count=invalid_min_count)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('999aa722-d624-4423-b813-0d1ac9884d7a')
    def test_min_count_non_integer(self):
        invalid_min_count = 2.5
        self.assertRaises(lib_exc.BadRequest, self._create_multiple_servers,
                          min_count=invalid_min_count)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a6f9c2ab-e060-4b82-b23c-4532cb9390ff')
    def test_max_count_less_than_one(self):
        invalid_max_count = 0
        self.assertRaises(lib_exc.BadRequest, self._create_multiple_servers,
                          max_count=invalid_max_count)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('9c5698d1-d7af-4c80-b971-9d403135eea2')
    def test_max_count_non_integer(self):
        invalid_max_count = 2.5
        self.assertRaises(lib_exc.BadRequest, self._create_multiple_servers,
                          max_count=invalid_max_count)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('476da616-f1ef-4271-a9b1-b9fc87727cdf')
    def test_max_count_less_than_min_count(self):
        min_count = 3
        max_count = 2
        self.assertRaises(lib_exc.BadRequest, self._create_multiple_servers,
                          min_count=min_count,
                          max_count=max_count)
