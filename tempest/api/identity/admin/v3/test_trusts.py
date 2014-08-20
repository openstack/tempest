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

import datetime
import re

from tempest.api.identity import base
from tempest import auth
from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import timeutils
from tempest import test

CONF = config.CONF


class BaseTrustsV3Test(base.BaseIdentityV3AdminTest):

    def setUp(self):
        super(BaseTrustsV3Test, self).setUp()
        # Use alt_username as the trustee
        if not CONF.identity_feature_enabled.trust:
            raise self.skipException("Trusts aren't enabled")

        self.trustee_username = CONF.identity.alt_username
        self.trust_id = None

    def tearDown(self):
        if self.trust_id:
            # Do the delete in tearDown not addCleanup - we want the test to
            # fail in the event there is a bug which causes undeletable trusts
            self.delete_trust()
        super(BaseTrustsV3Test, self).tearDown()

    def create_trustor_and_roles(self):
        # Get trustor project ID, use the admin project
        self.trustor_project_name = self.client.tenant_name
        self.trustor_project_id = self.get_tenant_by_name(
            self.trustor_project_name)['id']
        self.assertIsNotNone(self.trustor_project_id)

        # Create a trustor User
        self.trustor_username = data_utils.rand_name('user-')
        u_desc = self.trustor_username + 'description'
        u_email = self.trustor_username + '@testmail.xx'
        self.trustor_password = data_utils.rand_name('pass-')
        _, user = self.client.create_user(
            self.trustor_username,
            description=u_desc,
            password=self.trustor_password,
            email=u_email,
            project_id=self.trustor_project_id)
        self.trustor_user_id = user['id']

        # And two roles, one we'll delegate and one we won't
        self.delegated_role = data_utils.rand_name('DelegatedRole-')
        self.not_delegated_role = data_utils.rand_name('NotDelegatedRole-')

        _, role = self.client.create_role(self.delegated_role)
        self.delegated_role_id = role['id']

        _, role = self.client.create_role(self.not_delegated_role)
        self.not_delegated_role_id = role['id']

        # Assign roles to trustor
        self.client.assign_user_role(self.trustor_project_id,
                                     self.trustor_user_id,
                                     self.delegated_role_id)
        self.client.assign_user_role(self.trustor_project_id,
                                     self.trustor_user_id,
                                     self.not_delegated_role_id)

        # Get trustee user ID, use the demo user
        trustee_username = self.non_admin_client.user
        self.trustee_user_id = self.get_user_by_name(trustee_username)['id']
        self.assertIsNotNone(self.trustee_user_id)

        # Initialize a new client with the trustor credentials
        creds = auth.get_credentials(
            username=self.trustor_username,
            password=self.trustor_password,
            tenant_name=self.trustor_project_name)
        os = clients.Manager(
            credentials=creds,
            interface=self._interface)
        self.trustor_client = os.identity_v3_client

    def cleanup_user_and_roles(self):
        if self.trustor_user_id:
            self.client.delete_user(self.trustor_user_id)
        if self.delegated_role_id:
            self.client.delete_role(self.delegated_role_id)
        if self.not_delegated_role_id:
            self.client.delete_role(self.not_delegated_role_id)

    def create_trust(self, impersonate=True, expires=None):

        _, trust_create = self.trustor_client.create_trust(
            trustor_user_id=self.trustor_user_id,
            trustee_user_id=self.trustee_user_id,
            project_id=self.trustor_project_id,
            role_names=[self.delegated_role],
            impersonation=impersonate,
            expires_at=expires)
        self.trust_id = trust_create['id']
        return trust_create

    def validate_trust(self, trust, impersonate=True, expires=None,
                       summary=False):
        self.assertIsNotNone(trust['id'])
        self.assertEqual(impersonate, trust['impersonation'])
        # FIXME(shardy): ref bug #1246383 we can't check the
        # microsecond component of the expiry time, because mysql
        # <5.6.4 doesn't support microseconds.
        # expected format 2013-12-20T16:08:36.036987Z
        if expires is not None:
            expires_nousec = re.sub(r'\.([0-9]){6}Z', '', expires)
            self.assertTrue(trust['expires_at'].startswith(expires_nousec))
        else:
            self.assertIsNone(trust['expires_at'])
        self.assertEqual(self.trustor_user_id, trust['trustor_user_id'])
        self.assertEqual(self.trustee_user_id, trust['trustee_user_id'])
        self.assertIn('v3/OS-TRUST/trusts', trust['links']['self'])
        self.assertEqual(self.trustor_project_id, trust['project_id'])
        if not summary:
            self.assertEqual(self.delegated_role, trust['roles'][0]['name'])
            self.assertEqual(1, len(trust['roles']))

    def get_trust(self):
        _, trust_get = self.trustor_client.get_trust(self.trust_id)
        return trust_get

    def validate_role(self, role):
        self.assertEqual(self.delegated_role_id, role['id'])
        self.assertEqual(self.delegated_role, role['name'])
        self.assertIn('v3/roles/%s' % self.delegated_role_id,
                      role['links']['self'])
        self.assertNotEqual(self.not_delegated_role_id, role['id'])
        self.assertNotEqual(self.not_delegated_role, role['name'])
        self.assertNotIn('v3/roles/%s' % self.not_delegated_role_id,
                         role['links']['self'])

    def check_trust_roles(self):
        # Check we find the delegated role
        _, roles_get = self.trustor_client.get_trust_roles(
            self.trust_id)
        self.assertEqual(1, len(roles_get))
        self.validate_role(roles_get[0])

        _, role_get = self.trustor_client.get_trust_role(
            self.trust_id, self.delegated_role_id)
        self.validate_role(role_get)

        _, role_get = self.trustor_client.check_trust_role(
            self.trust_id, self.delegated_role_id)

        # And that we don't find not_delegated_role
        self.assertRaises(exceptions.NotFound,
                          self.trustor_client.get_trust_role,
                          self.trust_id,
                          self.not_delegated_role_id)

        self.assertRaises(exceptions.NotFound,
                          self.trustor_client.check_trust_role,
                          self.trust_id,
                          self.not_delegated_role_id)

    def delete_trust(self):
        self.trustor_client.delete_trust(self.trust_id)
        self.assertRaises(exceptions.NotFound,
                          self.trustor_client.get_trust,
                          self.trust_id)
        self.trust_id = None


class TrustsV3TestJSON(BaseTrustsV3Test):
    _interface = 'json'

    def setUp(self):
        super(TrustsV3TestJSON, self).setUp()
        self.create_trustor_and_roles()
        self.addCleanup(self.cleanup_user_and_roles)

    @test.attr(type='smoke')
    def test_trust_impersonate(self):
        # Test case to check we can create, get and delete a trust
        # updates are not supported for trusts
        trust = self.create_trust()
        self.validate_trust(trust)

        trust_get = self.get_trust()
        self.validate_trust(trust_get)

        self.check_trust_roles()

    @test.attr(type='smoke')
    def test_trust_noimpersonate(self):
        # Test case to check we can create, get and delete a trust
        # with impersonation=False
        trust = self.create_trust(impersonate=False)
        self.validate_trust(trust, impersonate=False)

        trust_get = self.get_trust()
        self.validate_trust(trust_get, impersonate=False)

        self.check_trust_roles()

    @test.attr(type='smoke')
    def test_trust_expire(self):
        # Test case to check we can create, get and delete a trust
        # with an expiry specified
        expires_at = timeutils.utcnow() + datetime.timedelta(hours=1)
        expires_str = timeutils.isotime(at=expires_at, subsecond=True)

        trust = self.create_trust(expires=expires_str)
        self.validate_trust(trust, expires=expires_str)

        trust_get = self.get_trust()

        self.validate_trust(trust_get, expires=expires_str)

        self.check_trust_roles()

    @test.attr(type='smoke')
    def test_trust_expire_invalid(self):
        # Test case to check we can check an invlaid expiry time
        # is rejected with the correct error
        # with an expiry specified
        expires_str = 'bad.123Z'
        self.assertRaises(exceptions.BadRequest,
                          self.create_trust,
                          expires=expires_str)

    @test.attr(type='smoke')
    def test_get_trusts_query(self):
        self.create_trust()
        _, trusts_get = self.trustor_client.get_trusts(
            trustor_user_id=self.trustor_user_id)
        self.assertEqual(1, len(trusts_get))
        self.validate_trust(trusts_get[0], summary=True)

    @test.attr(type='smoke')
    def test_get_trusts_all(self):
        self.create_trust()
        _, trusts_get = self.client.get_trusts()
        trusts = [t for t in trusts_get
                  if t['id'] == self.trust_id]
        self.assertEqual(1, len(trusts))
        self.validate_trust(trusts[0], summary=True)
