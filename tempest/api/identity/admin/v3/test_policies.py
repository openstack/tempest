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
from tempest.common.utils import data_utils
from tempest.test import attr


class PoliciesTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    def _delete_policy(self, policy_id):
        resp, _ = self.policy_client.delete_policy(policy_id)
        self.assertEqual(204, resp.status)

    @attr(type='smoke')
    def test_list_policies(self):
        # Test to list policies
        policy_ids = list()
        fetched_ids = list()
        for _ in range(3):
            blob = data_utils.rand_name('BlobName-')
            policy_type = data_utils.rand_name('PolicyType-')
            resp, policy = self.policy_client.create_policy(blob,
                                                            policy_type)
            # Delete the Policy at the end of this method
            self.addCleanup(self._delete_policy, policy['id'])
            policy_ids.append(policy['id'])
        # List and Verify Policies
        resp, body = self.policy_client.list_policies()
        self.assertEqual(resp['status'], '200')
        for p in body:
            fetched_ids.append(p['id'])
        missing_pols = [p for p in policy_ids if p not in fetched_ids]
        self.assertEqual(0, len(missing_pols))

    @attr(type='smoke')
    def test_create_update_delete_policy(self):
        # Test to update policy
        blob = data_utils.rand_name('BlobName-')
        policy_type = data_utils.rand_name('PolicyType-')
        resp, policy = self.policy_client.create_policy(blob, policy_type)
        self.addCleanup(self._delete_policy, policy['id'])
        self.assertIn('id', policy)
        self.assertIn('type', policy)
        self.assertIn('blob', policy)
        self.assertIsNotNone(policy['id'])
        self.assertEqual(blob, policy['blob'])
        self.assertEqual(policy_type, policy['type'])
        resp, fetched_policy = self.policy_client.get_policy(policy['id'])
        self.assertEqual(resp['status'], '200')
        # Update policy
        update_type = data_utils.rand_name('UpdatedPolicyType-')
        resp, data = self.policy_client.update_policy(
            policy['id'], type=update_type)
        self.assertIn('type', data)
        # Assertion for updated value with fetched value
        resp, fetched_policy = self.policy_client.get_policy(policy['id'])
        self.assertIn('id', fetched_policy)
        self.assertIn('blob', fetched_policy)
        self.assertIn('type', fetched_policy)
        self.assertEqual(fetched_policy['id'], policy['id'])
        self.assertEqual(fetched_policy['blob'], policy['blob'])
        self.assertEqual(update_type, fetched_policy['type'])


class PoliciesTestXML(PoliciesTestJSON):
    _interface = 'xml'
