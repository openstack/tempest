# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 IBM
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

import httplib2
import json
import logging

from lxml import etree

from tempest.common.rest_client import RestClient
from tempest.common.rest_client import RestClientXML
from tempest import exceptions
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json


XMLNS = "http://docs.openstack.org/identity/api/v2.0"


class AdminClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(AdminClientXML, self).__init__(config, username, password,
                                             auth_url, tenant_name)
        self.service = self.config.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(xml_to_json(child))
        return array

    def _parse_body(self, body):
        json = xml_to_json(body)
        return json

    def has_admin_extensions(self):
        """
        Returns True if the KSADM Admin Extensions are supported
        False otherwise
        """
        if hasattr(self, '_has_admin_extensions'):
            return self._has_admin_extensions
        resp, body = self.list_roles()
        self._has_admin_extensions = ('status' in resp and resp.status != 503)
        return self._has_admin_extensions

    def create_role(self, name):
        """Create a role."""
        create_role = Element("role", xmlns=XMLNS, name=name)
        resp, body = self.post('OS-KSADM/roles', str(Document(create_role)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def create_tenant(self, name, **kwargs):
        """
        Create a tenant
        name (required): New tenant name
        description: Description of new tenant (default is none)
        enabled <true|false>: Initial tenant status (default is true)
        """
        en = kwargs.get('enabled', 'true')
        create_tenant = Element("tenant",
                                xmlns=XMLNS,
                                name=name,
                                description=kwargs.get('description', ''),
                                enabled=str(en).lower())
        resp, body = self.post('tenants', str(Document(create_tenant)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('OS-KSADM/roles/%s' % str(role_id),
                                 self.headers)
        return resp, body

    def list_user_roles(self, tenant_id, user_id):
        """Returns a list of roles assigned to a user for a tenant."""
        url = '/tenants/%s/users/%s/roles' % (tenant_id, user_id)
        resp, body = self.get(url, self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def assign_user_role(self, tenant_id, user_id, role_id):
        """Add roles to a user on a tenant."""
        resp, body = self.put('/tenants/%s/users/%s/roles/OS-KSADM/%s' %
                              (tenant_id, user_id, role_id), '', self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def remove_user_role(self, tenant_id, user_id, role_id):
        """Removes a role assignment for a user on a tenant."""
        return self.delete('/tenants/%s/users/%s/roles/OS-KSADM/%s' %
                           (tenant_id, user_id, role_id), self.headers)

    def delete_tenant(self, tenant_id):
        """Delete a tenant."""
        resp, body = self.delete('tenants/%s' % str(tenant_id), self.headers)
        return resp, body

    def get_tenant(self, tenant_id):
        """Get tenant details."""
        resp, body = self.get('tenants/%s' % str(tenant_id), self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def list_roles(self):
        """Returns roles."""
        resp, body = self.get('OS-KSADM/roles', self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def list_tenants(self):
        """Returns tenants."""
        resp, body = self.get('tenants', self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_tenant_by_name(self, tenant_name):
        resp, tenants = self.list_tenants()
        for tenant in tenants:
            if tenant['name'] == tenant_name:
                return tenant
        raise exceptions.NotFound('No such tenant')

    def update_tenant(self, tenant_id, **kwargs):
        """Updates a tenant."""
        resp, body = self.get_tenant(tenant_id)
        name = kwargs.get('name', body['name'])
        desc = kwargs.get('description', body['description'])
        en = kwargs.get('enabled', body['enabled'])
        update_tenant = Element("tenant",
                                xmlns=XMLNS,
                                id=tenant_id,
                                name=name,
                                description=desc,
                                enabled=str(en).lower())

        resp, body = self.post('tenants/%s' % tenant_id,
                               str(Document(update_tenant)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def create_user(self, name, password, tenant_id, email):
        """Create a user."""
        create_user = Element("user",
                              xmlns=XMLNS,
                              name=name,
                              password=password,
                              tenantId=tenant_id,
                              email=email)
        resp, body = self.post('users', str(Document(create_user)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_user(self, user_id):
        """Delete a user."""
        resp, body = self.delete("users/%s" % user_id, self.headers)
        return resp, body

    def get_users(self):
        """Get the list of users."""
        resp, body = self.get("users", self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def enable_disable_user(self, user_id, enabled):
        """Enables or disables a user."""
        enable_user = Element("user", enabled=str(enabled).lower())
        resp, body = self.put('users/%s/enabled' % user_id,
                              str(Document(enable_user)), self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def delete_token(self, token_id):
        """Delete a token."""
        resp, body = self.delete("tokens/%s" % token_id, self.headers)
        return resp, body

    def list_users_for_tenant(self, tenant_id):
        """List users for a Tenant."""
        resp, body = self.get('/tenants/%s/users' % tenant_id, self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_user_by_username(self, tenant_id, username):
        resp, users = self.list_users_for_tenant(tenant_id)
        for user in users:
            if user['name'] == username:
                return user
        raise exceptions.NotFound('No such user')

    def create_service(self, name, type, **kwargs):
        """Create a service."""
        OS_KSADM = "http://docs.openstack.org/identity/api/ext/OS-KSADM/v1.0"
        create_service = Element("service",
                                 xmlns=OS_KSADM,
                                 name=name,
                                 type=type,
                                 description=kwargs.get('description'))
        resp, body = self.post('OS-KSADM/services',
                               str(Document(create_service)),
                               self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def get_service(self, service_id):
        """Get Service."""
        url = '/OS-KSADM/services/%s' % service_id
        resp, body = self.get(url, self.headers)
        body = self._parse_body(etree.fromstring(body))
        return resp, body

    def delete_service(self, service_id):
        """Delete Service."""
        url = '/OS-KSADM/services/%s' % service_id
        return self.delete(url, self.headers)


class TokenClientXML(RestClientXML):

    def __init__(self, config):
        self.auth_url = config.identity.auth_url
        self.config = config

    def auth(self, user, password, tenant):
        passwordCreds = Element("passwordCredentials",
                                username=user,
                                password=password)
        auth = Element("auth", tenantName=tenant)
        auth.append(passwordCreds)
        headers = {'Content-Type': 'application/xml'}
        resp, body = self.post(self.auth_url, headers=headers,
                               body=str(Document(auth)))
        return resp, body

    def request(self, method, url, headers=None, body=None):
        """A simple HTTP request interface."""
        dscv = self.config.identity.disable_ssl_certificate_validation
        self.http_obj = httplib2.Http(disable_ssl_certificate_validation=dscv)
        if headers is None:
            headers = {}

        resp, resp_body = self.http_obj.request(url, method,
                                                headers=headers, body=body)

        if resp.status in (401, 403):
            resp_body = json.loads(resp_body)
            raise exceptions.Unauthorized(resp_body['error']['message'])

        return resp, resp_body

    def get_token(self, user, password, tenant):
        resp, body = self.auth(user, password, tenant)
        if resp['status'] != '202':
            body = json.loads(body)
            access = body['access']
            token = access['token']
            return token['id']
