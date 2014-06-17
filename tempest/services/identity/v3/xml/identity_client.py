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

import json

from lxml import etree

from tempest.common import rest_client
from tempest.common import xml_utils as common
from tempest import config
from tempest import exceptions

CONF = config.CONF

XMLNS = "http://docs.openstack.org/identity/api/v3"


class IdentityV3ClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(IdentityV3ClientXML, self).__init__(auth_provider)
        self.service = CONF.identity.catalog_type
        self.endpoint_url = 'adminURL'
        self.api_version = "v3"

    def _parse_projects(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "project":
                array.append(common.xml_to_json(child))
        return array

    def _parse_domains(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "domain":
                array.append(common.xml_to_json(child))
        return array

    def _parse_groups(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "group":
                array.append(common.xml_to_json(child))
        return array

    def _parse_group_users(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "user":
                array.append(common.xml_to_json(child))
        return array

    def _parse_roles(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "role":
                array.append(common.xml_to_json(child))
        return array

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(common.xml_to_json(child))
        return array

    def _parse_body(self, body):
        _json = common.xml_to_json(body)
        return _json

    def create_user(self, user_name, **kwargs):
        """Creates a user."""
        password = kwargs.get('password', None)
        email = kwargs.get('email', None)
        en = kwargs.get('enabled', 'true')
        project_id = kwargs.get('project_id', None)
        description = kwargs.get('description', None)
        domain_id = kwargs.get('domain_id', 'default')
        post_body = common.Element("user",
                                   xmlns=XMLNS,
                                   name=user_name,
                                   password=password,
                                   description=description,
                                   email=email,
                                   enabled=str(en).lower(),
                                   project_id=project_id,
                                   domain_id=domain_id)
        resp, body = self.post('users', str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def update_user(self, user_id, name, **kwargs):
        """Updates a user."""
        resp, body = self.get_user(user_id)
        email = kwargs.get('email', body['email'])
        en = kwargs.get('enabled', body['enabled'])
        project_id = kwargs.get('project_id', body['project_id'])
        description = kwargs.get('description', body['description'])
        domain_id = kwargs.get('domain_id', body['domain_id'])
        update_user = common.Element("user",
                                     xmlns=XMLNS,
                                     name=name,
                                     email=email,
                                     project_id=project_id,
                                     domain_id=domain_id,
                                     description=description,
                                     enabled=str(en).lower())
        resp, body = self.patch('users/%s' % user_id,
                                str(common.Document(update_user)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_user_projects(self, user_id):
        """Lists the projects on which a user has roles assigned."""
        resp, body = self.get('users/%s/projects' % user_id)
        body = self._parse_projects(etree.fromstring(body))
        return resp, body

    def get_users(self):
        """Get the list of users."""
        resp, body = self.get("users")
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_user(self, user_id):
        """GET a user."""
        resp, body = self.get("users/%s" % user_id)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_user(self, user_id):
        """Deletes a User."""
        resp, body = self.delete("users/%s" % user_id)
        return resp, body

    def create_project(self, name, **kwargs):
        """Creates a project."""
        description = kwargs.get('description', None)
        en = kwargs.get('enabled', 'true')
        domain_id = kwargs.get('domain_id', 'default')
        post_body = common.Element("project",
                                   xmlns=XMLNS,
                                   description=description,
                                   domain_id=domain_id,
                                   enabled=str(en).lower(),
                                   name=name)
        resp, body = self.post('projects',
                               str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_projects(self):
        """Get the list of projects."""
        resp, body = self.get("projects")
        body = self._parse_projects(etree.fromstring(body))
        return resp, body

    def update_project(self, project_id, **kwargs):
        """Updates a Project."""
        resp, body = self.get_project(project_id)
        name = kwargs.get('name', body['name'])
        desc = kwargs.get('description', body['description'])
        en = kwargs.get('enabled', body['enabled'])
        domain_id = kwargs.get('domain_id', body['domain_id'])
        post_body = common.Element("project",
                                   xmlns=XMLNS,
                                   name=name,
                                   description=desc,
                                   enabled=str(en).lower(),
                                   domain_id=domain_id)
        resp, body = self.patch('projects/%s' % project_id,
                                str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_project(self, project_id):
        """GET a Project."""
        resp, body = self.get("projects/%s" % project_id)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_project(self, project_id):
        """Delete a project."""
        resp, body = self.delete('projects/%s' % str(project_id))
        return resp, body

    def create_role(self, name):
        """Create a Role."""
        post_body = common.Element("role",
                                   xmlns=XMLNS,
                                   name=name)
        resp, body = self.post('roles', str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_role(self, role_id):
        """GET a Role."""
        resp, body = self.get('roles/%s' % str(role_id))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_roles(self):
        """Get the list of Roles."""
        resp, body = self.get("roles")
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def update_role(self, name, role_id):
        """Updates a Role."""
        post_body = common.Element("role",
                                   xmlns=XMLNS,
                                   name=name)
        resp, body = self.patch('roles/%s' % str(role_id),
                                str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('roles/%s' % str(role_id))
        return resp, body

    def assign_user_role(self, project_id, user_id, role_id):
        """Add roles to a user on a tenant."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), '')
        return resp, body

    def create_domain(self, name, **kwargs):
        """Creates a domain."""
        description = kwargs.get('description', None)
        en = kwargs.get('enabled', True)
        post_body = common.Element("domain",
                                   xmlns=XMLNS,
                                   name=name,
                                   description=description,
                                   enabled=str(en).lower())
        resp, body = self.post('domains', str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_domains(self):
        """Get the list of domains."""
        resp, body = self.get("domains")
        body = self._parse_domains(etree.fromstring(body))
        return resp, body

    def delete_domain(self, domain_id):
        """Delete a domain."""
        resp, body = self.delete('domains/%s' % domain_id)
        return resp, body

    def update_domain(self, domain_id, **kwargs):
        """Updates a domain."""
        resp, body = self.get_domain(domain_id)
        description = kwargs.get('description', body['description'])
        en = kwargs.get('enabled', body['enabled'])
        name = kwargs.get('name', body['name'])
        post_body = common.Element("domain",
                                   xmlns=XMLNS,
                                   name=name,
                                   description=description,
                                   enabled=str(en).lower())
        resp, body = self.patch('domains/%s' % domain_id,
                                str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_domain(self, domain_id):
        """Get Domain details."""
        resp, body = self.get('domains/%s' % domain_id)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_token(self, resp_token):
        """GET a Token Details."""
        headers = {'Content-Type': 'application/xml',
                   'Accept': 'application/xml',
                   'X-Subject-Token': resp_token}
        resp, body = self.get("auth/tokens", headers=headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_token(self, resp_token):
        """Delete a Given Token."""
        headers = {'X-Subject-Token': resp_token}
        resp, body = self.delete("auth/tokens", headers=headers)
        return resp, body

    def create_group(self, name, **kwargs):
        """Creates a group."""
        description = kwargs.get('description', None)
        domain_id = kwargs.get('domain_id', 'default')
        project_id = kwargs.get('project_id', None)
        post_body = common.Element("group",
                                   xmlns=XMLNS,
                                   name=name,
                                   description=description,
                                   domain_id=domain_id,
                                   project_id=project_id)
        resp, body = self.post('groups', str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_group(self, group_id):
        """Get group details."""
        resp, body = self.get('groups/%s' % group_id)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def update_group(self, group_id, **kwargs):
        """Updates a group."""
        resp, body = self.get_group(group_id)
        name = kwargs.get('name', body['name'])
        description = kwargs.get('description', body['description'])
        post_body = common.Element("group",
                                   xmlns=XMLNS,
                                   name=name,
                                   description=description)
        resp, body = self.patch('groups/%s' % group_id,
                                str(common.Document(post_body)))
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_group(self, group_id):
        """Delete a group."""
        resp, body = self.delete('groups/%s' % group_id)
        return resp, body

    def add_group_user(self, group_id, user_id):
        """Add user into group."""
        resp, body = self.put('groups/%s/users/%s' % (group_id, user_id), '')
        return resp, body

    def list_group_users(self, group_id):
        """List users in group."""
        resp, body = self.get('groups/%s/users' % group_id)
        body = self._parse_group_users(etree.fromstring(body))
        return resp, body

    def list_user_groups(self, user_id):
        """Lists the groups which a user belongs to."""
        resp, body = self.get('users/%s/groups' % user_id)
        body = self._parse_groups(etree.fromstring(body))
        return resp, body

    def delete_group_user(self, group_id, user_id):
        """Delete user in group."""
        resp, body = self.delete('groups/%s/users/%s' % (group_id, user_id))
        return resp, body

    def assign_user_role_on_project(self, project_id, user_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), '')
        return resp, body

    def assign_user_role_on_domain(self, domain_id, user_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/users/%s/roles/%s' %
                              (domain_id, user_id, role_id), '')
        return resp, body

    def list_user_roles_on_project(self, project_id, user_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/users/%s/roles' %
                              (project_id, user_id))
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def list_user_roles_on_domain(self, domain_id, user_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/users/%s/roles' %
                              (domain_id, user_id))
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def revoke_role_from_user_on_project(self, project_id, user_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/users/%s/roles/%s' %
                                 (project_id, user_id, role_id))
        return resp, body

    def revoke_role_from_user_on_domain(self, domain_id, user_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/users/%s/roles/%s' %
                                 (domain_id, user_id, role_id))
        return resp, body

    def assign_group_role_on_project(self, project_id, group_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/groups/%s/roles/%s' %
                              (project_id, group_id, role_id), '')
        return resp, body

    def assign_group_role_on_domain(self, domain_id, group_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/groups/%s/roles/%s' %
                              (domain_id, group_id, role_id), '')
        return resp, body

    def list_group_roles_on_project(self, project_id, group_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/groups/%s/roles' %
                              (project_id, group_id))
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def list_group_roles_on_domain(self, domain_id, group_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/groups/%s/roles' %
                              (domain_id, group_id))
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def revoke_role_from_group_on_project(self, project_id, group_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/groups/%s/roles/%s' %
                                 (project_id, group_id, role_id))
        return resp, body

    def revoke_role_from_group_on_domain(self, domain_id, group_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/groups/%s/roles/%s' %
                                 (domain_id, group_id, role_id))
        return resp, body


class V3TokenClientXML(rest_client.RestClient):
    TYPE = "xml"

    def __init__(self):
        super(V3TokenClientXML, self).__init__(None)
        auth_url = CONF.identity.uri_v3
        if not auth_url and CONF.identity_feature_enabled.api_v3:
            raise exceptions.InvalidConfiguration('you must specify a v3 uri '
                                                  'if using the v3 identity '
                                                  'api')
        if 'auth/tokens' not in auth_url:
            auth_url = auth_url.rstrip('/') + '/auth/tokens'

        self.auth_url = auth_url

    def auth(self, user=None, password=None, tenant=None, user_type='id',
             domain=None, token=None):
        """
        :param user: user id or name, as specified in user_type
        :param domain: the user and tenant domain
        :param token: a token to re-scope.

        Accepts different combinations of credentials. Restrictions:
        - tenant and domain are only name (no id)
        - user domain and tenant domain are assumed identical
        - domain scope is not supported here
        Sample sample valid combinations:
        - token
        - token, tenant, domain
        - user_id, password
        - username, password, domain
        - username, password, tenant, domain
        Validation is left to the server side.
        """

        methods = common.Element('methods')
        identity = common.Element('identity')

        if token:
            method = common.Element('method')
            method.append(common.Text('token'))
            methods.append(method)

            token = common.Element('token', id=token)
            identity.append(token)

        if user and password:
            if user_type == 'id':
                _user = common.Element('user', id=user, password=password)
            else:
                _user = common.Element('user', name=user, password=password)
            if domain is not None:
                _domain = common.Element('domain', name=domain)
                _user.append(_domain)

            password = common.Element('password')
            password.append(_user)
            method = common.Element('method')
            method.append(common.Text('password'))
            methods.append(method)
            identity.append(password)

        identity.append(methods)

        auth = common.Element('auth')
        auth.append(identity)

        if tenant is not None:
            project = common.Element('project', name=tenant)
            _domain = common.Element('domain', name=domain)
            project.append(_domain)
            scope = common.Element('scope')
            scope.append(project)
            auth.append(scope)

        resp, body = self.post(self.auth_url, body=str(common.Document(auth)))
        return resp, body

    def request(self, method, url, extra_headers=False, headers=None,
                body=None):
        """A simple HTTP request interface."""
        if headers is None:
            # Always accept 'json', for xml token client too.
            # Because XML response is not easily
            # converted to the corresponding JSON one
            headers = self.get_headers(accept_type="json")
        elif extra_headers:
            try:
                headers.update(self.get_headers(accept_type="json"))
            except (ValueError, TypeError):
                headers = self.get_headers(accept_type="json")
        resp, resp_body = self.http_obj.request(url, method,
                                                headers=headers, body=body)
        self._log_request(method, url, resp)

        if resp.status in [401, 403]:
            resp_body = json.loads(resp_body)
            raise exceptions.Unauthorized(resp_body['error']['message'])
        elif resp.status not in [200, 201, 204]:
            raise exceptions.IdentityError(
                'Unexpected status code {0}'.format(resp.status))

        return resp, json.loads(resp_body)

    def get_token(self, user, password, tenant, domain='Default',
                  auth_data=False):
        """
        :param user: username
        Returns (token id, token data) for supplied credentials
        """
        resp, body = self.auth(user, password, tenant, user_type='name',
                               domain=domain)

        token = resp.get('x-subject-token')
        if auth_data:
            return token, body['token']
        else:
            return token
