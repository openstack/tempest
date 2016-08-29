# Copyright 2015 Red Hat Inc.
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

from tempest.api.identity import base
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest import test


class DomainsNegativeTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('1f3fbff5-4e44-400d-9ca1-d953f05f609b')
    def test_delete_active_domain(self):
        d_name = data_utils.rand_name('domain')
        d_desc = data_utils.rand_name('domain-desc')
        domain = self.domains_client.create_domain(
            d_name,
            description=d_desc)['domain']
        domain_id = domain['id']

        self.addCleanup(self.delete_domain, domain_id)

        # domain need to be disabled before deleting
        self.assertRaises(lib_exc.Forbidden, self.domains_client.delete_domain,
                          domain_id)

    @test.attr(type=['negative'])
    @test.idempotent_id('9018461d-7d24-408d-b3fe-ae37e8cd5c9e')
    def test_create_domain_with_empty_name(self):
        # Domain name should not be empty
        self.assertRaises(lib_exc.BadRequest,
                          self.domains_client.create_domain, name='')

    @test.attr(type=['negative'])
    @test.idempotent_id('37b1bbf2-d664-4785-9a11-333438586eae')
    def test_create_domain_with_name_length_over_64(self):
        # Domain name length should not ne greater than 64 characters
        d_name = 'a' * 65
        self.assertRaises(lib_exc.BadRequest,
                          self.domains_client.create_domain, d_name)

    @test.attr(type=['negative'])
    @test.idempotent_id('43781c07-764f-4cf2-a405-953c1916f605')
    def test_delete_non_existent_domain(self):
        # Attempt to delete a non existent domain should fail
        self.assertRaises(lib_exc.NotFound, self.domains_client.delete_domain,
                          data_utils.rand_uuid_hex())

    @test.attr(type=['negative'])
    @test.idempotent_id('e6f9e4a2-4f36-4be8-bdbc-4e199ae29427')
    def test_domain_create_duplicate(self):
        domain_name = data_utils.rand_name('domain-dup')
        domain = self.domains_client.create_domain(domain_name)['domain']
        domain_id = domain['id']
        self.addCleanup(self.delete_domain, domain_id)
        # Domain name should be unique
        self.assertRaises(
            lib_exc.Conflict, self.domains_client.create_domain, domain_name)
