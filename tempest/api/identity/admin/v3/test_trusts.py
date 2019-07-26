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

from oslo_utils import timeutils

from tempest.api.identity import base
from tempest import clients
from tempest.common import credentials_factory as common_creds
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class TrustsV3TestJSON(base.BaseIdentityV3AdminTest):

    @classmethod
    def skip_checks(cls):
        super(TrustsV3TestJSON, cls).skip_checks()
        if not CONF.identity_feature_enabled.trust:
            raise cls.skipException("Trusts aren't enabled")
        if CONF.identity_feature_enabled.immutable_user_source:
            raise cls.skipException('Skipped because environment has an '
                                    'immutable user source and solely '
                                    'provides read-only access to users.')

    def setUp(self):
        super(TrustsV3TestJSON, self).setUp()
        # Use alt_username as the trustee
        self.trust_id = None
        self.create_trustor_and_roles()

    def tearDown(self):
        if self.trust_id:
            # Do the delete in tearDown not addCleanup - we want the test to
            # fail in the event there is a bug which causes undeletable trusts
            self.delete_trust()
        super(TrustsV3TestJSON, self).tearDown()

    def create_trustor_and_roles(self):
        # create a project that trusts will be granted on
        trustor_project_name = data_utils.rand_name(
            name=self.__class__.__name__)
        project = self.projects_client.create_project(
            trustor_project_name,
            domain_id=CONF.identity.default_domain_id)['project']
        self.trustor_project_id = project['id']
        self.addCleanup(self.projects_client.delete_project, project['id'])
        self.assertIsNotNone(self.trustor_project_id)

        # Create a trustor User
        trustor_username = data_utils.rand_name('user')
        u_desc = trustor_username + 'description'
        u_email = trustor_username + '@testmail.xx'
        trustor_password = data_utils.rand_password()
        user = self.users_client.create_user(
            name=trustor_username,
            description=u_desc,
            password=trustor_password,
            email=u_email,
            project_id=self.trustor_project_id,
            domain_id=CONF.identity.default_domain_id)['user']
        self.addCleanup(self.users_client.delete_user, user['id'])
        self.trustor_user_id = user['id']

        # And two roles, one we'll delegate and one we won't
        self.delegated_role = data_utils.rand_name('DelegatedRole')
        self.not_delegated_role = data_utils.rand_name('NotDelegatedRole')

        role = self.roles_client.create_role(name=self.delegated_role)['role']
        self.addCleanup(self.roles_client.delete_role, role['id'])
        self.delegated_role_id = role['id']

        role = self.roles_client.create_role(
            name=self.not_delegated_role)['role']
        self.addCleanup(self.roles_client.delete_role, role['id'])
        self.not_delegated_role_id = role['id']

        # Assign roles to trustor
        self.roles_client.create_user_role_on_project(
            self.trustor_project_id,
            self.trustor_user_id,
            self.delegated_role_id)
        self.roles_client.create_user_role_on_project(
            self.trustor_project_id,
            self.trustor_user_id,
            self.not_delegated_role_id)

        # Get trustee user ID, use the demo user
        trustee_username = self.non_admin_client.user
        self.trustee_user_id = self.get_user_by_name(trustee_username)['id']
        self.assertIsNotNone(self.trustee_user_id)

        # Initialize a new client with the trustor credentials
        creds = common_creds.get_credentials(
            identity_version='v3',
            username=trustor_username,
            password=trustor_password,
            user_domain_id=CONF.identity.default_domain_id,
            tenant_name=trustor_project_name,
            project_domain_id=CONF.identity.default_domain_id,
            domain_id=CONF.identity.default_domain_id)
        os = clients.Manager(credentials=creds)
        self.trustor_client = os.trusts_client

    def create_trust(self, impersonate=True, expires=None):

        trust_create = self.trustor_client.create_trust(
            trustor_user_id=self.trustor_user_id,
            trustee_user_id=self.trustee_user_id,
            project_id=self.trustor_project_id,
            roles=[{'name': self.delegated_role}],
            impersonation=impersonate,
            expires_at=expires)['trust']
        self.trust_id = trust_create['id']
        return trust_create

    def validate_trust(self, trust, impersonate=True, expires=None,
                       summary=False):
        self.assertIsNotNone(trust['id'])
        self.assertEqual(impersonate, trust['impersonation'])
        if expires is not None:
            # Omit microseconds component of the expiry time
            trust_expires_at = re.sub(r'\.([0-9]){6}', '', trust['expires_at'])
            self.assertEqual(expires, trust_expires_at)
        else:
            self.assertIsNone(trust['expires_at'])
        self.assertEqual(self.trustor_user_id, trust['trustor_user_id'])
        self.assertEqual(self.trustee_user_id, trust['trustee_user_id'])
        self.assertIn('v3/OS-TRUST/trusts', trust['links']['self'])
        self.assertEqual(self.trustor_project_id, trust['project_id'])
        if not summary:
            self.assertEqual(self.delegated_role, trust['roles'][0]['name'])
            self.assertEqual(1, len(trust['roles']))

    def show_trust(self):
        trust_get = self.trustor_client.show_trust(self.trust_id)['trust']
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
        roles_get = self.trustor_client.list_trust_roles(
            self.trust_id)['roles']
        self.assertEqual(1, len(roles_get))
        self.validate_role(roles_get[0])

        role_get = self.trustor_client.show_trust_role(
            self.trust_id, self.delegated_role_id)['role']
        self.validate_role(role_get)

        role_get = self.trustor_client.check_trust_role(
            self.trust_id, self.delegated_role_id)

        # And that we don't find not_delegated_role
        self.assertRaises(lib_exc.NotFound,
                          self.trustor_client.show_trust_role,
                          self.trust_id,
                          self.not_delegated_role_id)

        self.assertRaises(lib_exc.NotFound,
                          self.trustor_client.check_trust_role,
                          self.trust_id,
                          self.not_delegated_role_id)

    def delete_trust(self):
        self.trustor_client.delete_trust(self.trust_id)
        self.assertRaises(lib_exc.NotFound,
                          self.trustor_client.show_trust,
                          self.trust_id)
        self.trust_id = None

    @decorators.idempotent_id('5a0a91a4-baef-4a14-baba-59bf4d7fcace')
    def test_trust_impersonate(self):
        # Test case to check we can create, get and delete a trust
        # updates are not supported for trusts
        trust = self.create_trust()
        self.validate_trust(trust)

        trust_get = self.show_trust()
        self.validate_trust(trust_get)

        self.check_trust_roles()

    @decorators.idempotent_id('ed2a8779-a7ac-49dc-afd7-30f32f936ed2')
    def test_trust_noimpersonate(self):
        # Test case to check we can create, get and delete a trust
        # with impersonation=False
        trust = self.create_trust(impersonate=False)
        self.validate_trust(trust, impersonate=False)

        trust_get = self.show_trust()
        self.validate_trust(trust_get, impersonate=False)

        self.check_trust_roles()

    @decorators.idempotent_id('0ed14b66-cefd-4b5c-a964-65759453e292')
    def test_trust_expire(self):
        # Test case to check we can create, get and delete a trust
        # with an expiry specified
        expires_at = timeutils.utcnow() + datetime.timedelta(hours=1)
        # NOTE(ylobankov) In some cases the expiry time may be rounded up
        # because of microseconds. In fact, it depends on database and its
        # version. At least MySQL 5.6.16 does this.
        # For example, when creating a trust, we will set the expiry time of
        # the trust to 2015-02-17T17:34:01.907051Z. However, if we make a GET
        # request on the trust, the response will contain the time rounded up
        # to 2015-02-17T17:34:02.000000Z. That is why we set microsecond to
        # 0 when we invoke isoformat to avoid problems with rounding.
        expires_at = expires_at.replace(microsecond=0)
        # NOTE(ekhugen) Python datetime does not support military timezones
        # since we used UTC we'll add the Z so our compare works.
        expires_str = expires_at.isoformat() + 'Z'

        trust = self.create_trust(expires=expires_str)
        self.validate_trust(trust, expires=expires_str)

        trust_get = self.show_trust()

        self.validate_trust(trust_get, expires=expires_str)

        self.check_trust_roles()

    @decorators.idempotent_id('3e48f95d-e660-4fa9-85e0-5a3d85594384')
    def test_trust_expire_invalid(self):
        # Test case to check we can check an invalid expiry time
        # is rejected with the correct error
        # with an expiry specified
        expires_str = 'bad.123Z'
        self.assertRaises(lib_exc.BadRequest,
                          self.create_trust,
                          expires=expires_str)

    @decorators.idempotent_id('6268b345-87ca-47c0-9ce3-37792b43403a')
    def test_get_trusts_query(self):
        self.create_trust()
        trusts_get = self.trustor_client.list_trusts(
            trustor_user_id=self.trustor_user_id)['trusts']
        self.assertEqual(1, len(trusts_get))
        self.validate_trust(trusts_get[0], summary=True)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('4773ebd5-ecbf-4255-b8d8-b63e6f72b65d')
    def test_get_trusts_all(self):

        # Simple function that can be used for cleanup
        def set_scope(auth_provider, scope):
            auth_provider.scope = scope

        self.create_trust()
        # Listing trusts can be done by trustor, by trustee, or without
        # any filter if scoped to a project, so we must ensure token scope is
        # project for this test.
        original_scope = self.os_admin.auth_provider.scope
        set_scope(self.os_admin.auth_provider, 'project')
        self.addCleanup(set_scope, self.os_admin.auth_provider, original_scope)
        trusts_get = self.trusts_client.list_trusts()['trusts']
        trusts = [t for t in trusts_get
                  if t['id'] == self.trust_id]
        self.assertEqual(1, len(trusts))
        self.validate_trust(trusts[0], summary=True)
