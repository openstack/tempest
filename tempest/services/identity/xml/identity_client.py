# Copyright 2012 IBM Corp.
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
from tempest.common import xml_utils as xml
from tempest import config
from tempest.services.identity.json import identity_client

CONF = config.CONF

XMLNS = "http://docs.openstack.org/identity/api/v2.0"


class IdentityClientXML(identity_client.IdentityClientJSON):
    TYPE = "xml"

    def create_role(self, name):
        """Create a role."""
        create_role = xml.Element("role", xmlns=XMLNS, name=name)
        resp, body = self.post('OS-KSADM/roles',
                               str(xml.Document(create_role)))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def get_role(self, role_id):
        """Get a role by its id."""
        resp, body = self.get('OS-KSADM/roles/%s' % role_id)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def create_tenant(self, name, **kwargs):
        """
        Create a tenant
        name (required): New tenant name
        description: Description of new tenant (default is none)
        enabled <true|false>: Initial tenant status (default is true)
        """
        en = kwargs.get('enabled', 'true')
        create_tenant = xml.Element("tenant",
                                    xmlns=XMLNS,
                                    name=name,
                                    description=kwargs.get('description', ''),
                                    enabled=str(en).lower())
        resp, body = self.post('tenants', str(xml.Document(create_tenant)))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def list_tenants(self):
        """Returns tenants."""
        resp, body = self.get('tenants')
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def update_tenant(self, tenant_id, **kwargs):
        """Updates a tenant."""
        _, body = self.get_tenant(tenant_id)
        name = kwargs.get('name', body['name'])
        desc = kwargs.get('description', body['description'])
        en = kwargs.get('enabled', body['enabled'])
        update_tenant = xml.Element("tenant",
                                    xmlns=XMLNS,
                                    id=tenant_id,
                                    name=name,
                                    description=desc,
                                    enabled=str(en).lower())

        resp, body = self.post('tenants/%s' % tenant_id,
                               str(xml.Document(update_tenant)))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def create_user(self, name, password, tenant_id, email, **kwargs):
        """Create a user."""
        create_user = xml.Element("user",
                                  xmlns=XMLNS,
                                  name=name,
                                  password=password,
                                  email=email)
        if tenant_id:
            create_user.add_attr('tenantId', tenant_id)
        if 'enabled' in kwargs:
            create_user.add_attr('enabled', str(kwargs['enabled']).lower())

        resp, body = self.post('users', str(xml.Document(create_user)))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def update_user(self, user_id, **kwargs):
        """Updates a user."""
        if 'enabled' in kwargs:
            kwargs['enabled'] = str(kwargs['enabled']).lower()
        update_user = xml.Element("user", xmlns=XMLNS, **kwargs)

        resp, body = self.put('users/%s' % user_id,
                              str(xml.Document(update_user)))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def enable_disable_user(self, user_id, enabled):
        """Enables or disables a user."""
        enable_user = xml.Element("user", enabled=str(enabled).lower())
        resp, body = self.put('users/%s/enabled' % user_id,
                              str(xml.Document(enable_user)))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def create_service(self, name, service_type, **kwargs):
        """Create a service."""
        OS_KSADM = "http://docs.openstack.org/identity/api/ext/OS-KSADM/v1.0"
        create_service = xml.Element("service",
                                     xmlns=OS_KSADM,
                                     name=name,
                                     type=service_type,
                                     description=kwargs.get('description'))
        resp, body = self.post('OS-KSADM/services',
                               str(xml.Document(create_service)))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def update_user_password(self, user_id, new_pass):
        """Update User Password."""
        put_body = xml.Element("user",
                               id=user_id,
                               password=new_pass)
        resp, body = self.put('users/%s/OS-KSADM/password' % user_id,
                              str(xml.Document(put_body)))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def list_extensions(self):
        """List all the extensions."""
        resp, body = self.get('/extensions')
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)


class TokenClientXML(identity_client.TokenClientJSON):
    TYPE = "xml"

    def auth(self, user, password, tenant=None):
        passwordCreds = xml.Element('passwordCredentials',
                                    username=user,
                                    password=password)
        auth_kwargs = {}
        if tenant:
            auth_kwargs['tenantName'] = tenant
        auth = xml.Element('auth', **auth_kwargs)
        auth.append(passwordCreds)
        resp, body = self.post(self.auth_url, body=str(xml.Document(auth)))
        return resp, body['access']

    def auth_token(self, token_id, tenant=None):
        tokenCreds = xml.Element('token', id=token_id)
        auth_kwargs = {}
        if tenant:
            auth_kwargs['tenantName'] = tenant
        auth = xml.Element('auth', **auth_kwargs)
        auth.append(tokenCreds)
        resp, body = self.post(self.auth_url, body=str(xml.Document(auth)))
        return resp, body['access']
