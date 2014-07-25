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
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class MultipleCreateV3NegativeTest(base.BaseV3ComputeTest):
    _name = 'multiple-create-negative-test'

    def _generate_name(self):
        return data_utils.rand_name(self._name)

    def _create_multiple_servers(self, name=None, wait_until=None, **kwargs):
        """
        This is the right way to create_multiple servers and manage to get the
        created servers into the servers list to be cleaned up after all.
        """
        kwargs['name'] = kwargs.get('name', self._generate_name())
        resp, body = self.create_test_server(**kwargs)

        return resp, body

    @test.attr(type=['negative', 'gate'])
    def test_min_count_less_than_one(self):
        invalid_min_count = 0
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          min_count=invalid_min_count)

    @test.attr(type=['negative', 'gate'])
    def test_min_count_non_integer(self):
        invalid_min_count = 2.5
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          min_count=invalid_min_count)

    @test.attr(type=['negative', 'gate'])
    def test_max_count_less_than_one(self):
        invalid_max_count = 0
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          max_count=invalid_max_count)

    @test.attr(type=['negative', 'gate'])
    def test_max_count_non_integer(self):
        invalid_max_count = 2.5
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          max_count=invalid_max_count)

    @test.attr(type=['negative', 'gate'])
    def test_max_count_less_than_min_count(self):
        min_count = 3
        max_count = 2
        self.assertRaises(exceptions.BadRequest, self._create_multiple_servers,
                          min_count=min_count,
                          max_count=max_count)
