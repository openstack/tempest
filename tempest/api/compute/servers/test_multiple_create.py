# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest import test


class MultipleCreateTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'
    _name = 'multiple-create-test'

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

    @test.attr(type='gate')
    def test_multiple_create(self):
        resp, body = self._create_multiple_servers(wait_until='ACTIVE',
                                                   min_count=1,
                                                   max_count=2)
        # NOTE(maurosr): do status response check and also make sure that
        # reservation_id is not in the response body when the request send
        # contains return_reservation_id=False
        self.assertEqual('202', resp['status'])
        self.assertNotIn('reservation_id', body)

    @test.attr(type='gate')
    def test_multiple_create_with_reservation_return(self):
        resp, body = self._create_multiple_servers(wait_until='ACTIVE',
                                                   min_count=1,
                                                   max_count=2,
                                                   return_reservation_id=True)
        self.assertEqual(resp['status'], '202')
        self.assertIn('reservation_id', body)


class MultipleCreateTestXML(MultipleCreateTestJSON):
    _interface = 'xml'
