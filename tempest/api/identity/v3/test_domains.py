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

from tempest.api.identity import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class DefaultDomainTestJSON(base.BaseIdentityV3Test):
    """Test identity default domains"""

    @classmethod
    def setup_clients(cls):
        super(DefaultDomainTestJSON, cls).setup_clients()
        cls.domains_client = cls.os_primary.domains_client

    @classmethod
    def resource_setup(cls):
        super(DefaultDomainTestJSON, cls).resource_setup()
        cls.domain_id = CONF.identity.default_domain_id

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('17a5de24-e6a0-4e4a-a9ee-d85b6e5612b5')
    def test_default_domain_exists(self):
        """Test showing default domain"""
        domain = self.domains_client.show_domain(self.domain_id)['domain']
        self.assertTrue(domain['enabled'])
