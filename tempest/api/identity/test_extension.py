# Copyright 2014 NEC Corporation
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
from tempest import test


class ExtensionTestJSON(base.BaseIdentityV2AdminTest):

    @test.attr(type='gate')
    @test.idempotent_id('85f3f661-f54c-4d48-b563-72ae952b9383')
    def test_list_extensions(self):
        # List all the extensions
        body = self.non_admin_client.list_extensions()
        self.assertNotEmpty(body)
        keys = ['name', 'updated', 'alias', 'links',
                'namespace', 'description']
        for value in body:
            for key in keys:
                self.assertIn(key, value)
