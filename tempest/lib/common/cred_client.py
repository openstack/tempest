# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc

from oslo_log import log as logging

from tempest.lib import auth
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.identity.v2 import identity_client as v2_identity

LOG = logging.getLogger(__name__)


class CredsClient(object, metaclass=abc.ABCMeta):
    """This class is a wrapper around the identity clients

     to provide a single interface for managing credentials in both v2 and v3
     cases. It's not bound to created credentials, only to a specific set of
     admin credentials used for generating credentials.
    """

    def __init__(self, identity_client, projects_client, users_client,
                 roles_client):
        # The client implies version and credentials
        self.identity_client = identity_client
        self.users_client = users_client
        self.projects_client = projects_client
        self.roles_client = roles_client

    def create_user(self, username, password, project=None, email=None):
        params = {'name': username,
                  'password': password}
        # with keystone v3, a default project is not required
        if project:
            params[self.project_id_param] = project['id']
        # email is not a first-class attribute of a user
        if email:
            params['email'] = email
        user = self.users_client.create_user(**params)
        if 'user' in user:
            user = user['user']
        return user

    def delete_user(self, user_id):
        self.users_client.delete_user(user_id)

    @abc.abstractmethod
    def create_project(self, name, description):
        pass

    def _check_role_exists(self, role_name):
        try:
            roles = self._list_roles()
            lc_role_name = role_name.lower()
            role = next(r for r in roles if r['name'].lower() == lc_role_name)
        except StopIteration:
            return None
        return role

    def create_user_role(self, role_name):
        if not self._check_role_exists(role_name):
            self.roles_client.create_role(name=role_name)

    def assign_user_role(self, user, project, role_name):
        role = self._check_role_exists(role_name)
        if not role:
            msg = 'No "%s" role found' % role_name
            raise lib_exc.NotFound(msg)
        try:
            self.roles_client.create_user_role_on_project(project['id'],
                                                          user['id'],
                                                          role['id'])
        except lib_exc.Conflict:
            LOG.debug("Role %s already assigned on project %s for user %s",
                      role['id'], project['id'], user['id'])

    @abc.abstractmethod
    def get_credentials(
            self, user, project, password, domain=None, system=None):
        """Produces a Credentials object from the details provided

        :param user: a user dict
        :param project: a project dict or None if using domain or system scope
        :param password: the password as a string
        :param domain: a domain dict
        :param system: a system dict
        :return: a Credentials object with all the available credential details
        """
        pass

    def _list_roles(self):
        roles = self.roles_client.list_roles()['roles']
        return roles


class V2CredsClient(CredsClient):
    project_id_param = 'tenantId'

    def __init__(self, identity_client, projects_client, users_client,
                 roles_client):
        super(V2CredsClient, self).__init__(identity_client,
                                            projects_client,
                                            users_client,
                                            roles_client)

    def create_project(self, name, description):
        tenant = self.projects_client.create_tenant(
            name=name, description=description)['tenant']
        return tenant

    def delete_project(self, project_id):
        self.projects_client.delete_tenant(project_id)

    def get_credentials(
        self, user, project, password, domain=None, system=None):
        # User and project already include both ID and name here,
        # so there's no need to use the fill_in mode
        return auth.get_credentials(
            auth_url=None,
            fill_in=False,
            identity_version='v2',
            username=user['name'], user_id=user['id'],
            tenant_name=project['name'], tenant_id=project['id'],
            password=password)


class V3CredsClient(CredsClient):
    project_id_param = 'project_id'

    def __init__(self, identity_client, projects_client, users_client,
                 roles_client, domains_client, domain_name):
        super(V3CredsClient, self).__init__(identity_client, projects_client,
                                            users_client, roles_client)
        self.domains_client = domains_client

        try:
            # Domain names must be unique, in any case a list is returned,
            # selecting the first (and only) element
            self.creds_domain = self.domains_client.list_domains(
                name=domain_name)['domains'][0]
        except lib_exc.NotFound:
            # TODO(andrea) we could probably create the domain on the fly
            msg = "Requested domain %s could not be found" % domain_name
            raise lib_exc.InvalidCredentials(msg)

    def create_project(self, name, description):
        project = self.projects_client.create_project(
            name=name, description=description,
            domain_id=self.creds_domain['id'])['project']
        return project

    def delete_project(self, project_id):
        self.projects_client.delete_project(project_id)

    def create_domain(self, name, description):
        domain = self.domains_client.create_domain(
            name=name, description=description)['domain']
        return domain

    def delete_domain(self, domain_id):
        self.domains_client.update_domain(domain_id, enabled=False)
        self.domains_client.delete_domain(domain_id)

    def create_user(self, username, password, project=None, email=None,
                    domain_id=None):
        params = {'name': username,
                  'password': password,
                  'domain_id': domain_id or self.creds_domain['id']}
        # with keystone v3, a default project is not required
        if project:
            params[self.project_id_param] = project['id']
        # email is not a first-class attribute of a user
        if email:
            params['email'] = email
        user = self.users_client.create_user(**params)
        if 'user' in user:
            user = user['user']
        return user

    def get_credentials(
            self, user, project, password, domain=None, system=None):
        # User, project and domain already include both ID and name here,
        # so there's no need to use the fill_in mode.
        # NOTE(andreaf) We need to set all fields in the returned credentials.
        # Scope is then used to pick only those relevant for the type of
        # token needed by each service client.
        if project:
            project_name = project['name']
            project_id = project['id']
        else:
            project_name = None
            project_id = None
        if domain:
            domain_name = domain['name']
            domain_id = domain['id']
        else:
            domain_name = self.creds_domain['name']
            domain_id = self.creds_domain['id']
        return auth.get_credentials(
            auth_url=None,
            fill_in=False,
            identity_version='v3',
            username=user['name'], user_id=user['id'],
            project_name=project_name, project_id=project_id,
            password=password,
            project_domain_id=self.creds_domain['id'],
            project_domain_name=self.creds_domain['name'],
            domain_id=domain_id,
            domain_name=domain_name,
            system=system)

    def assign_user_role_on_domain(self, user, role_name, domain=None):
        """Assign the specified role on a domain

        :param user: a user dict
        :param role_name: name of the role to be assigned
        :param domain: (optional) The domain to assign the role on. If not
                                  specified the default domain of cred_client
        """
        # NOTE(andreaf) This method is very specific to the v3 case, and
        # because of that it's not defined in the parent class.
        if domain is None:
            domain = self.creds_domain
        role = self._check_role_exists(role_name)
        if not role:
            msg = 'No "%s" role found' % role_name
            raise lib_exc.NotFound(msg)
        try:
            self.roles_client.create_user_role_on_domain(
                domain['id'], user['id'], role['id'])
        except lib_exc.Conflict:
            LOG.debug("Role %s already assigned on domain %s for user %s",
                      role['id'], domain['id'], user['id'])

    def assign_user_role_on_system(self, user, role_name):
        """Assign the specified role on the system

        :param user: a user dict
        :param role_name: name of the role to be assigned
        """
        role = self._check_role_exists(role_name)
        if not role:
            msg = 'No "%s" role found' % role_name
            raise lib_exc.NotFound(msg)
        try:
            self.roles_client.create_user_role_on_system(
                user['id'], role['id'])
        except lib_exc.Conflict:
            LOG.debug("Role %s already assigned on the system for user %s",
                      role['id'], user['id'])


def get_creds_client(identity_client,
                     projects_client,
                     users_client,
                     roles_client,
                     domains_client=None,
                     project_domain_name=None):
    if isinstance(identity_client, v2_identity.IdentityClient):
        return V2CredsClient(identity_client, projects_client, users_client,
                             roles_client)
    else:
        return V3CredsClient(identity_client, projects_client, users_client,
                             roles_client, domains_client, project_domain_name)
