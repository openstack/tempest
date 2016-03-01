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
import six

from tempest.lib import auth
from tempest.lib import exceptions as lib_exc
from tempest.services.identity.v2.json import identity_client as v2_identity

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class CredsClient(object):
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

    def create_user(self, username, password, project, email):
        user = self.users_client.create_user(
            username, password, project['id'], email)
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
            role = next(r for r in roles if r['name'] == role_name)
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
            self._assign_user_role(project, user, role)
        except lib_exc.Conflict:
            LOG.debug("Role %s already assigned on project %s for user %s" % (
                role['id'], project['id'], user['id']))

    @abc.abstractmethod
    def get_credentials(self, user, project, password):
        """Produces a Credentials object from the details provided

        :param user: a user dict
        :param project: a project dict
        :param password: the password as a string
        :return: a Credentials object with all the available credential details
        """
        pass

    def _list_roles(self):
        roles = self.roles_client.list_roles()['roles']
        return roles


class V2CredsClient(CredsClient):

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

    def get_credentials(self, user, project, password):
        # User and project already include both ID and name here,
        # so there's no need to use the fill_in mode
        return auth.get_credentials(
            auth_url=None,
            fill_in=False,
            identity_version='v2',
            username=user['name'], user_id=user['id'],
            tenant_name=project['name'], tenant_id=project['id'],
            password=password)

    def _assign_user_role(self, project, user, role):
        self.roles_client.assign_user_role(project['id'], user['id'],
                                           role['id'])


class V3CredsClient(CredsClient):

    def __init__(self, identity_client, projects_client, users_client,
                 roles_client, domains_client, domain_name):
        super(V3CredsClient, self).__init__(identity_client, projects_client,
                                            users_client, roles_client)
        self.domains_client = domains_client

        try:
            # Domain names must be unique, in any case a list is returned,
            # selecting the first (and only) element
            self.creds_domain = self.domains_client.list_domains(
                params={'name': domain_name})['domains'][0]
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

    def get_credentials(self, user, project, password):
        # User, project and domain already include both ID and name here,
        # so there's no need to use the fill_in mode.
        return auth.get_credentials(
            auth_url=None,
            fill_in=False,
            identity_version='v3',
            username=user['name'], user_id=user['id'],
            project_name=project['name'], project_id=project['id'],
            password=password,
            project_domain_id=self.creds_domain['id'],
            project_domain_name=self.creds_domain['name'])

    def _assign_user_role(self, project, user, role):
        self.roles_client.assign_user_role_on_project(project['id'],
                                                      user['id'],
                                                      role['id'])


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
