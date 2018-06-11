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
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class RolesV3TestJSON(base.BaseIdentityV3AdminTest):

    @classmethod
    def resource_setup(cls):
        super(RolesV3TestJSON, cls).resource_setup()
        cls.roles = list()
        for _ in range(3):
            role_name = data_utils.rand_name(name='role')
            role = cls.roles_client.create_role(name=role_name)['role']
            cls.addClassResourceCleanup(cls.roles_client.delete_role,
                                        role['id'])
            cls.roles.append(role)
        u_name = data_utils.rand_name('user')
        u_desc = '%s description' % u_name
        u_email = '%s@testmail.tm' % u_name
        cls.u_password = data_utils.rand_password()
        cls.domain = cls.create_domain()
        cls.project = cls.projects_client.create_project(
            data_utils.rand_name('project'),
            description=data_utils.rand_name('project-desc'),
            domain_id=cls.domain['id'])['project']
        cls.addClassResourceCleanup(cls.projects_client.delete_project,
                                    cls.project['id'])
        cls.group_body = cls.groups_client.create_group(
            name=data_utils.rand_name('Group'), project_id=cls.project['id'],
            domain_id=cls.domain['id'])['group']
        cls.addClassResourceCleanup(cls.groups_client.delete_group,
                                    cls.group_body['id'])
        cls.user_body = cls.users_client.create_user(
            name=u_name, description=u_desc, password=cls.u_password,
            email=u_email, project_id=cls.project['id'],
            domain_id=cls.domain['id'])['user']
        cls.addClassResourceCleanup(cls.users_client.delete_user,
                                    cls.user_body['id'])
        cls.role = cls.roles_client.create_role(
            name=data_utils.rand_name('Role'))['role']
        cls.addClassResourceCleanup(cls.roles_client.delete_role,
                                    cls.role['id'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('18afc6c0-46cf-4911-824e-9989cc056c3a')
    def test_role_create_update_show_list(self):
        r_name = data_utils.rand_name('Role')
        role = self.roles_client.create_role(name=r_name)['role']
        self.addCleanup(self.roles_client.delete_role, role['id'])
        self.assertIn('name', role)
        self.assertEqual(role['name'], r_name)

        new_name = data_utils.rand_name('NewRole')
        updated_role = self.roles_client.update_role(role['id'],
                                                     name=new_name)['role']
        self.assertIn('name', updated_role)
        self.assertIn('id', updated_role)
        self.assertIn('links', updated_role)
        self.assertNotEqual(r_name, updated_role['name'])

        new_role = self.roles_client.show_role(role['id'])['role']
        self.assertEqual(new_name, new_role['name'])
        self.assertEqual(updated_role['id'], new_role['id'])

        roles = self.roles_client.list_roles()['roles']
        self.assertIn(role['id'], [r['id'] for r in roles])

    @decorators.idempotent_id('c6b80012-fe4a-498b-9ce8-eb391c05169f')
    def test_grant_list_revoke_role_to_user_on_project(self):
        self.roles_client.create_user_role_on_project(self.project['id'],
                                                      self.user_body['id'],
                                                      self.role['id'])

        roles = self.roles_client.list_user_roles_on_project(
            self.project['id'], self.user_body['id'])['roles']

        self.assertEqual(1, len(roles))
        self.assertEqual(self.role['id'], roles[0]['id'])

        self.roles_client.check_user_role_existence_on_project(
            self.project['id'], self.user_body['id'], self.role['id'])

        self.roles_client.delete_role_from_user_on_project(
            self.project['id'], self.user_body['id'], self.role['id'])

    @decorators.idempotent_id('6c9a2940-3625-43a3-ac02-5dcec62ef3bd')
    def test_grant_list_revoke_role_to_user_on_domain(self):
        self.roles_client.create_user_role_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])

        roles = self.roles_client.list_user_roles_on_domain(
            self.domain['id'], self.user_body['id'])['roles']

        self.assertEqual(1, len(roles))
        self.assertEqual(self.role['id'], roles[0]['id'])

        self.roles_client.check_user_role_existence_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])

        self.roles_client.delete_role_from_user_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])

    @decorators.idempotent_id('cbf11737-1904-4690-9613-97bcbb3df1c4')
    def test_grant_list_revoke_role_to_group_on_project(self):
        # Grant role to group on project
        self.roles_client.create_group_role_on_project(
            self.project['id'], self.group_body['id'], self.role['id'])
        # List group roles on project
        roles = self.roles_client.list_group_roles_on_project(
            self.project['id'], self.group_body['id'])['roles']

        self.assertEqual(1, len(roles))
        self.assertEqual(self.role['id'], roles[0]['id'])

        # Add user to group, and insure user has role on project
        self.groups_client.add_group_user(self.group_body['id'],
                                          self.user_body['id'])
        self.addCleanup(self.groups_client.delete_group_user,
                        self.group_body['id'], self.user_body['id'])
        body = self.token.auth(user_id=self.user_body['id'],
                               password=self.u_password,
                               user_domain_name=self.domain['name'],
                               project_name=self.project['name'],
                               project_domain_name=self.domain['name'])
        roles = body['token']['roles']
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]['id'], self.role['id'])

        self.roles_client.check_role_from_group_on_project_existence(
            self.project['id'], self.group_body['id'], self.role['id'])

        # Revoke role to group on project
        self.roles_client.delete_role_from_group_on_project(
            self.project['id'], self.group_body['id'], self.role['id'])

    @decorators.idempotent_id('4bf8a70b-e785-413a-ad53-9f91ce02faa7')
    def test_grant_list_revoke_role_to_group_on_domain(self):
        self.roles_client.create_group_role_on_domain(
            self.domain['id'], self.group_body['id'], self.role['id'])

        roles = self.roles_client.list_group_roles_on_domain(
            self.domain['id'], self.group_body['id'])['roles']

        self.assertEqual(1, len(roles))
        self.assertEqual(self.role['id'], roles[0]['id'])

        self.roles_client.check_role_from_group_on_domain_existence(
            self.domain['id'], self.group_body['id'], self.role['id'])

        self.roles_client.delete_role_from_group_on_domain(
            self.domain['id'], self.group_body['id'], self.role['id'])

    @decorators.idempotent_id('f5654bcc-08c4-4f71-88fe-05d64e06de94')
    def test_list_roles(self):
        # Return a list of all roles
        body = self.roles_client.list_roles()['roles']
        found = [role for role in body if role in self.roles]
        self.assertEqual(len(found), len(self.roles))

    def _create_implied_role(self, prior_role_id, implies_role_id,
                             ignore_not_found=False):
        self.roles_client.create_role_inference_rule(
            prior_role_id, implies_role_id)
        if ignore_not_found:
            self.addCleanup(
                test_utils.call_and_ignore_notfound_exc,
                self.roles_client.delete_role_inference_rule,
                prior_role_id,
                implies_role_id)
        else:
            self.addCleanup(
                self.roles_client.delete_role_inference_rule,
                prior_role_id,
                implies_role_id)

    @decorators.idempotent_id('c90c316c-d706-4728-bcba-eb1912081b69')
    def test_implied_roles_create_check_show_delete(self):
        prior_role_id = self.roles[0]['id']
        implies_role_id = self.roles[1]['id']

        # Create an inference rule from prior_role to implies_role
        self._create_implied_role(prior_role_id, implies_role_id,
                                  ignore_not_found=True)

        # Check if the inference rule exists
        self.roles_client.check_role_inference_rule(
            prior_role_id, implies_role_id)

        # Show the inference rule and check its elements
        resp_body = self.roles_client.show_role_inference_rule(
            prior_role_id, implies_role_id)
        self.assertIn('role_inference', resp_body)
        role_inference = resp_body['role_inference']
        for key1 in ['prior_role', 'implies']:
            self.assertIn(key1, role_inference)
            for key2 in ['id', 'links', 'name']:
                self.assertIn(key2, role_inference[key1])

        # Delete the inference rule
        self.roles_client.delete_role_inference_rule(
            prior_role_id, implies_role_id)
        # Check if the inference rule no longer exists
        self.assertRaises(
            lib_exc.NotFound,
            self.roles_client.show_role_inference_rule,
            prior_role_id,
            implies_role_id)

    @decorators.idempotent_id('dc6f5959-b74d-4e30-a9e5-a8255494ff00')
    def test_roles_hierarchy(self):
        # Create inference rule from "roles[0]" to "role[1]"
        self._create_implied_role(
            self.roles[0]['id'], self.roles[1]['id'])

        # Create inference rule from "roles[0]" to "role[2]"
        self._create_implied_role(
            self.roles[0]['id'], self.roles[2]['id'])

        # Create inference rule from "roles[2]" to "role"
        self._create_implied_role(
            self.roles[2]['id'], self.role['id'])

        # Listing inferences rules from "roles[2]" should only return "role"
        rules = self.roles_client.list_role_inferences_rules(
            self.roles[2]['id'])['role_inference']
        self.assertEqual(1, len(rules['implies']))
        self.assertEqual(self.role['id'], rules['implies'][0]['id'])

        # Listing inferences rules from "roles[0]" should return "roles[1]" and
        # "roles[2]" (only direct rules are listed)
        rules = self.roles_client.list_role_inferences_rules(
            self.roles[0]['id'])['role_inference']
        implies_ids = [role['id'] for role in rules['implies']]
        self.assertEqual(2, len(implies_ids))
        self.assertIn(self.roles[1]['id'], implies_ids)
        self.assertIn(self.roles[2]['id'], implies_ids)

    @decorators.idempotent_id('c8828027-df48-4021-95df-b65b92c7429e')
    def test_assignments_for_implied_roles_create_delete(self):
        # Create a grant using "roles[0]"
        self.roles_client.create_user_role_on_project(
            self.project['id'], self.user_body['id'], self.roles[0]['id'])
        self.addCleanup(
            self.roles_client.delete_role_from_user_on_project,
            self.project['id'], self.user_body['id'], self.roles[0]['id'])

        # Create an inference rule from "roles[0]" to "roles[1]"
        self._create_implied_role(self.roles[0]['id'], self.roles[1]['id'],
                                  ignore_not_found=True)

        # In the effective list of role assignments, both prior role and
        # implied role should be present. This means that a user can
        # authenticate using both roles (both roles will be present
        # in the token).
        params = {'scope.project.id': self.project['id'],
                  'user.id': self.user_body['id']}
        role_assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertEqual(2, len(role_assignments))

        roles_ids = [assignment['role']['id']
                     for assignment in role_assignments]
        self.assertIn(self.roles[0]['id'], roles_ids)
        self.assertIn(self.roles[1]['id'], roles_ids)

        # After deleting the implied role, only the assignment with "roles[0]"
        # should be present.
        self.roles_client.delete_role_inference_rule(
            self.roles[0]['id'], self.roles[1]['id'])

        role_assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertEqual(1, len(role_assignments))

        roles_ids = [assignment['role']['id']
                     for assignment in role_assignments]
        self.assertIn(self.roles[0]['id'], roles_ids)

    @decorators.idempotent_id('d92a41d2-5501-497a-84bb-6e294330e8f8')
    def test_domain_roles_create_delete(self):
        domain_role = self.roles_client.create_role(
            name=data_utils.rand_name('domain_role'),
            domain_id=self.domain['id'])['role']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.roles_client.delete_role,
            domain_role['id'])

        domain_roles = self.roles_client.list_roles(
            domain_id=self.domain['id'])['roles']
        self.assertEqual(1, len(domain_roles))
        self.assertIn(domain_role, domain_roles)

        self.roles_client.delete_role(domain_role['id'])
        domain_roles = self.roles_client.list_roles(
            domain_id=self.domain['id'])['roles']
        self.assertEmpty(domain_roles)

    @decorators.idempotent_id('eb1e1c24-1bc4-4d47-9748-e127a1852c82')
    def test_implied_domain_roles(self):
        # Create two roles in the same domain
        domain_role1 = self.setup_test_role(domain_id=self.domain['id'])
        domain_role2 = self.setup_test_role(domain_id=self.domain['id'])

        # Check if we can create an inference rule from roles in the same
        # domain
        self._create_implied_role(domain_role1['id'], domain_role2['id'])

        # Create another role in a different domain
        domain2 = self.setup_test_domain()
        domain_role3 = self.setup_test_role(domain_id=domain2['id'])

        # Check if we can create cross domain implied roles
        self._create_implied_role(domain_role1['id'], domain_role3['id'])

        # Finally, we also should be able to create an implied from a
        # domain role to a global one
        self._create_implied_role(domain_role1['id'], self.role['id'])

        # The contrary is not true: we can't create an inference rule
        # from a global role to a domain role
        self.assertRaises(
            lib_exc.Forbidden,
            self.roles_client.create_role_inference_rule,
            self.role['id'],
            domain_role1['id'])

    @decorators.idempotent_id('3859df7e-5b78-4e4d-b10e-214c8953842a')
    def test_assignments_for_domain_roles(self):
        domain_role = self.setup_test_role(domain_id=self.domain['id'])

        # Create a grant using "domain_role"
        self.roles_client.create_user_role_on_project(
            self.project['id'], self.user_body['id'], domain_role['id'])
        self.addCleanup(
            self.roles_client.delete_role_from_user_on_project,
            self.project['id'], self.user_body['id'], domain_role['id'])

        # NOTE(rodrigods): Regular roles would appear in the effective
        # list of role assignments (meaning the role would be returned in
        # a token) as a result from the grant above. This is not the case
        # for domain roles, they should not appear in the effective role
        # assignments list.
        params = {'scope.project.id': self.project['id'],
                  'user.id': self.user_body['id']}
        role_assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertEmpty(role_assignments)

    @decorators.idempotent_id('3748c316-c18f-4b08-997b-c60567bc6235')
    def test_list_all_implied_roles(self):
        # Create inference rule from "roles[0]" to "roles[1]"
        self._create_implied_role(
            self.roles[0]['id'], self.roles[1]['id'])

        # Create inference rule from "roles[0]" to "roles[2]"
        self._create_implied_role(
            self.roles[0]['id'], self.roles[2]['id'])

        # Create inference rule from "roles[2]" to "role"
        self._create_implied_role(
            self.roles[2]['id'], self.role['id'])

        rules = self.roles_client.list_all_role_inference_rules()[
            'role_inferences']

        # NOTE(jaosorior): With the work related to the define-default-roles
        # blueprint, we now have 'admin', 'member' and 'reader' by default. So
        # we filter every other implied role to only take into account the ones
        # relates to this test.
        relevant_roles = (self.roles[0]['id'], self.roles[1]['id'],
                          self.roles[2]['id'], self.role['id'])

        def is_implied_role_relevant(rule):
            return any(r for r in rule['implies'] if r['id'] in relevant_roles)

        relevant_rules = filter(is_implied_role_relevant, rules)
        # Sort the rules by the number of inferences, since there should be 1
        # inference between "roles[2]" and "role" and 2 inferences for
        # "roles[0]": between "roles[1]" and "roles[2]".
        sorted_rules = sorted(relevant_rules, key=lambda r: len(r['implies']))

        self.assertEqual(2, len(sorted_rules))
        # Check that only 1 inference rule exists between "roles[2]" and "role"
        self.assertEqual(1, len(sorted_rules[0]['implies']))
        # Check that 2 inference rules exist for "roles[0]": one between
        # "roles[1]" and one between "roles[2]".
        self.assertEqual(2, len(sorted_rules[1]['implies']))

        # Check that "roles[2]" is the "prior_role" and that "role" is the
        # "implies" role.
        self.assertEqual(self.roles[2]['id'],
                         sorted_rules[0]['prior_role']['id'])
        self.assertEqual(self.role['id'],
                         sorted_rules[0]['implies'][0]['id'])

        # Check that "roles[0]" is the "prior_role" and that "roles[1]" and
        # "roles[2]" are the "implies" roles.
        self.assertEqual(self.roles[0]['id'],
                         sorted_rules[1]['prior_role']['id'])

        implies_ids = [r['id'] for r in sorted_rules[1]['implies']]
        self.assertIn(self.roles[1]['id'], implies_ids)
        self.assertIn(self.roles[2]['id'], implies_ids)
