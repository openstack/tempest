# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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

from urlparse import urlparse

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json

XMLNS = "http://docs.openstack.org/identity/api/v3"


class IdentityV3ClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(IdentityV3ClientXML, self).__init__(config, username, password,
                                                  auth_url, tenant_name)
        self.service = self.config.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def _parse_projects(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "project":
                array.append(xml_to_json(child))
        return array

    def _parse_domains(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "domain":
                array.append(xml_to_json(child))
        return array

    def _parse_roles(self, node):
        array = []
        for child in node.getchildren():
            tag_list = child.tag.split('}', 1)
            if tag_list[1] == "role":
                array.append(xml_to_json(child))
        return array

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(xml_to_json(child))
        return array

    def _parse_body(self, body):
        json = xml_to_json(body)
        return json

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class RestClient."""
        self._set_auth()
        self.base_url = self.base_url.replace(urlparse(self.base_url).path,
                                              "/v3")
        return super(IdentityV3ClientXML, self).request(method, url,
                                                        headers=headers,
                                                        body=body)

    def create_user(self, user_name, **kwargs):
        """Creates a user."""
        password = kwargs.get('password', None)
        email = kwargs.get('email', None)
        en = kwargs.get('enabled', 'true')
        project_id = kwargs.get('project_id', None)
        description = kwargs.get('description', None)
        domain_id = kwargs.get('domain_id', 'default')
        post_body = Element("user",
                            xmlns=XMLNS,
                            name=user_name,
                            password=password,
                            description=description,
                            email=email,
                            enabled=str(en).lower(),
                            project_id=project_id,
                            domain_id=domain_id)
        resp, body = self.post('users', str(Document(post_body)),
                               self.headers)
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
        update_user = Element("user",
                              xmlns=XMLNS,
                              name=name,
                              email=email,
                              project_id=project_id,
                              domain_id=domain_id,
                              description=description,
                              enabled=str(en).lower())
        resp, body = self.patch('users/%s' % user_id,
                                str(Document(update_user)),
                                self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_user_projects(self, user_id):
        """Lists the projects on which a user has roles assigned."""
        resp, body = self.get('users/%s/projects' % user_id, self.headers)
        body = self._parse_projects(etree.fromstring(body))
        return resp, body

    def get_users(self):
        """Get the list of users."""
        resp, body = self.get("users", self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_user(self, user_id):
        """GET a user."""
        resp, body = self.get("users/%s" % user_id, self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_user(self, user_id):
        """Deletes a User."""
        resp, body = self.delete("users/%s" % user_id, self.headers)
        return resp, body

    def create_project(self, name, **kwargs):
        """Creates a project."""
        description = kwargs.get('description', None)
        en = kwargs.get('enabled', 'true')
        domain_id = kwargs.get('domain_id', 'default')
        post_body = Element("project",
                            xmlns=XMLNS,
                            description=description,
                            domain_id=domain_id,
                            enabled=str(en).lower(),
                            name=name)
        resp, body = self.post('projects',
                               str(Document(post_body)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_project(self, project_id):
        """GET a Project."""
        resp, body = self.get("projects/%s" % project_id, self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_project(self, project_id):
        """Delete a project."""
        resp, body = self.delete('projects/%s' % str(project_id))
        return resp, body

    def create_role(self, name):
        """Create a Role."""
        post_body = Element("role",
                            xmlns=XMLNS,
                            name=name)
        resp, body = self.post('roles',
                               str(Document(post_body)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_role(self, role_id):
        """GET a Role."""
        resp, body = self.get('roles/%s' % str(role_id), self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def update_role(self, name, role_id):
        """Updates a Role."""
        post_body = Element("role",
                            xmlns=XMLNS,
                            name=name)
        resp, body = self.patch('roles/%s' % str(role_id),
                                str(Document(post_body)),
                                self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('roles/%s' % str(role_id),
                                 self.headers)
        return resp, body

    def assign_user_role(self, project_id, user_id, role_id):
        """Add roles to a user on a tenant."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), '', self.headers)
        return resp, body

    def create_domain(self, name, **kwargs):
        """Creates a domain."""
        description = kwargs.get('description', None)
        en = kwargs.get('enabled', True)
        post_body = Element("domain",
                            xmlns=XMLNS,
                            name=name,
                            description=description,
                            enabled=str(en).lower())
        resp, body = self.post('domains', str(Document(post_body)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_domains(self):
        """Get the list of domains."""
        resp, body = self.get("domains", self.headers)
        body = self._parse_domains(etree.fromstring(body))
        return resp, body

    def delete_domain(self, domain_id):
        """Delete a domain."""
        resp, body = self.delete('domains/%s' % domain_id, self.headers)
        return resp, body

    def update_domain(self, domain_id, **kwargs):
        """Updates a domain."""
        resp, body = self.get_domain(domain_id)
        description = kwargs.get('description', body['description'])
        en = kwargs.get('enabled', body['enabled'])
        name = kwargs.get('name', body['name'])
        post_body = Element("domain",
                            xmlns=XMLNS,
                            name=name,
                            description=description,
                            enabled=str(en).lower())
        resp, body = self.patch('domains/%s' % domain_id,
                                str(Document(post_body)),
                                self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_domain(self, domain_id):
        """Get Domain details."""
        resp, body = self.get('domains/%s' % domain_id, self.headers)
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
        post_body = Element("group",
                            xmlns=XMLNS,
                            name=name,
                            description=description,
                            domain_id=domain_id,
                            project_id=project_id)
        resp, body = self.post('groups', str(Document(post_body)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_group(self, group_id):
        """Delete a group."""
        resp, body = self.delete('groups/%s' % group_id, self.headers)
        return resp, body

    def assign_user_role_on_project(self, project_id, user_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), '',
                              self.headers)
        return resp, body

    def assign_user_role_on_domain(self, domain_id, user_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/users/%s/roles/%s' %
                              (domain_id, user_id, role_id), '',
                              self.headers)
        return resp, body

    def list_user_roles_on_project(self, project_id, user_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/users/%s/roles' %
                              (project_id, user_id), self.headers)
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def list_user_roles_on_domain(self, domain_id, user_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/users/%s/roles' %
                              (domain_id, user_id), self.headers)
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def revoke_role_from_user_on_project(self, project_id, user_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/users/%s/roles/%s' %
                                 (project_id, user_id, role_id), self.headers)
        return resp, body

    def revoke_role_from_user_on_domain(self, domain_id, user_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/users/%s/roles/%s' %
                                 (domain_id, user_id, role_id), self.headers)
        return resp, body

    def assign_group_role_on_project(self, project_id, group_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/groups/%s/roles/%s' %
                              (project_id, group_id, role_id), '',
                              self.headers)
        return resp, body

    def assign_group_role_on_domain(self, domain_id, group_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/groups/%s/roles/%s' %
                              (domain_id, group_id, role_id), '',
                              self.headers)
        return resp, body

    def list_group_roles_on_project(self, project_id, group_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/groups/%s/roles' %
                              (project_id, group_id), self.headers)
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def list_group_roles_on_domain(self, domain_id, group_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/groups/%s/roles' %
                              (domain_id, group_id), self.headers)
        body = self._parse_roles(etree.fromstring(body))
        return resp, body

    def revoke_role_from_group_on_project(self, project_id, group_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/groups/%s/roles/%s' %
                                 (project_id, group_id, role_id), self.headers)
        return resp, body

    def revoke_role_from_group_on_domain(self, domain_id, group_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/groups/%s/roles/%s' %
                                 (domain_id, group_id, role_id), self.headers)
        return resp, body


class V3TokenClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(V3TokenClientXML, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.identity.catalog_type
        self.endpoint_url = 'adminURL'

        auth_url = config.identity.uri

        if 'tokens' not in auth_url:
            auth_url = auth_url.rstrip('/') + '/tokens'

        self.auth_url = auth_url
        self.config = config

    def auth(self, user_id, password):
        user = Element('user',
                       id=user_id,
                       password=password)
        password = Element('password')
        password.append(user)

        method = Element('method')
        method.append(Text('password'))
        methods = Element('methods')
        methods.append(method)
        identity = Element('identity')
        identity.append(methods)
        identity.append(password)
        auth = Element('auth')
        auth.append(identity)
        headers = {'Content-Type': 'application/xml'}
        resp, body = self.post("auth/tokens", headers=headers,
                               body=str(Document(auth)))
        return resp, body

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class rest_client."""
        self._set_auth()
        self.base_url = self.base_url.replace(urlparse(self.base_url).path,
                                              "/v3")
        return super(V3TokenClientXML, self).request(method, url,
                                                     headers=headers,
                                                     body=body)
