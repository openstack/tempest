# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr


class DomainsTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    def _delete_domain(self, domain_id):
        # It is necessary to disable the domian before deleting,
        # or else it would result in unauthorized error
        _, body = self.v3_client.update_domain(domain_id, enabled=False)
        resp, _ = self.v3_client.delete_domain(domain_id)
        self.assertEqual(204, resp.status)

    @attr(type='smoke')
    def test_list_domains(self):
        #Test to list domains
        domain_ids = list()
        fetched_ids = list()
        for _ in range(3):
            _, domain = self.v3_client.create_domain(
                rand_name('domain-'), description=rand_name('domain-desc-'))
            # Delete the domian at the end of this method
            self.addCleanup(self._delete_domain, domain['id'])
            domain_ids.append(domain['id'])
        # List and Verify Domains
        resp, body = self.v3_client.list_domains()
        self.assertEqual(resp['status'], '200')
        for d in body:
            fetched_ids.append(d['id'])
        missing_doms = [d for d in domain_ids if d not in fetched_ids]
        self.assertEqual(0, len(missing_doms))


class DomainsTestXML(DomainsTestJSON):
    _interface = 'xml'
