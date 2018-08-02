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
import testtools

from tempest.api.identity import base
from tempest import clients
from tempest import config
from tempest.lib import auth
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class TestDefaultProjectId (base.BaseIdentityV3AdminTest):

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(TestDefaultProjectId, cls).setup_credentials()

    def _delete_domain(self, domain_id):
        # It is necessary to disable the domain before deleting,
        # or else it would result in unauthorized error
        self.domains_client.update_domain(domain_id, enabled=False)
        self.domains_client.delete_domain(domain_id)

    @testtools.skipIf(CONF.identity_feature_enabled.immutable_user_source,
                      'Skipped because environment has an '
                      'immutable user source and solely '
                      'provides read-only access to users.')
    @decorators.idempotent_id('d6110661-6a71-49a7-a453-b5e26640ff6d')
    def test_default_project_id(self):
        # create a domain
        dom_name = data_utils.rand_name('dom')
        domain_body = self.domains_client.create_domain(
            name=dom_name)['domain']
        dom_id = domain_body['id']
        self.addCleanup(self._delete_domain, dom_id)

        # create a project in the domain
        proj_body = self.setup_test_project(domain_id=dom_id)
        proj_id = proj_body['id']
        self.assertEqual(proj_body['domain_id'], dom_id,
                         "project " + proj_body['name'] +
                         "doesn't have domain id " + dom_id)

        # create a user in the domain, with the previous project as his
        # default project
        user_name = data_utils.rand_name('user')
        user_body = self.users_client.create_user(
            name=user_name,
            password=user_name,
            domain_id=dom_id,
            default_project_id=proj_id)['user']
        user_id = user_body['id']
        self.addCleanup(self.users_client.delete_user, user_id)
        self.assertEqual(user_body['domain_id'], dom_id,
                         "user " + user_name +
                         "doesn't have domain id " + dom_id)

        # get roles and find the admin role
        admin_role = self.get_role_by_name(CONF.identity.admin_role)
        admin_role_id = admin_role['id']

        # grant the admin role to the user on his project
        self.roles_client.create_user_role_on_project(proj_id, user_id,
                                                      admin_role_id)

        # create a new client with user's credentials (NOTE: unscoped token!)
        creds = auth.KeystoneV3Credentials(username=user_name,
                                           password=user_name,
                                           user_domain_name=dom_name)
        auth_provider = clients.get_auth_provider(creds)
        creds = auth_provider.fill_credentials()
        admin_client = clients.Manager(credentials=creds)

        # verify the user's token and see that it is scoped to the project
        token, _ = admin_client.auth_provider.get_auth()
        result = admin_client.identity_v3_client.show_token(token)['token']
        self.assertEqual(result['project']['domain']['id'], dom_id)
        self.assertEqual(result['project']['id'], proj_id)
