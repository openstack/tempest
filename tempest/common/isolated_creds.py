# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp.
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

import keystoneclient.v2_0.client

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class IsolatedCreds(object):

    def __init__(self, name, tempest_client=True, interface='json',
                 password='pass'):
        self.isolated_creds = {}
        self.name = name
        self.config = config.TempestConfig()
        self.tempest_client = tempest_client
        self.interface = interface
        self.password = password
        self.admin_client = self._get_identity_admin_client()

    def _get_keystone_client(self):
        username = self.config.identity.admin_username
        password = self.config.identity.admin_password
        tenant_name = self.config.identity.admin_tenant_name
        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation
        return keystoneclient.v2_0.client.Client(username=username,
                                                 password=password,
                                                 tenant_name=tenant_name,
                                                 auth_url=auth_url,
                                                 insecure=dscv)

    def _get_identity_admin_client(self):
        """
        Returns an instance of the Identity Admin API client
        """
        if self.tempest_client:
            os = clients.AdminManager(interface=self.interface)
            admin_client = os.identity_client
        else:
            admin_client = self._get_keystone_client()
        return admin_client

    def _create_tenant(self, name, description):
        if self.tempest_client:
            resp, tenant = self.admin_client.create_tenant(
                name=name, description=description)
        else:
            tenant = self.admin_client.tenants.create(name,
                                                      description=description)
        return tenant

    def _get_tenant_by_name(self, name):
        if self.tempest_client:
            resp, tenant = self.admin_client.get_tenant_by_name(name)
        else:
            tenants = self.admin_client.tenants.list()
            for ten in tenants:
                if ten['name'] == name:
                    tenant = ten
            raise exceptions.NotFound('No such tenant')
        return tenant

    def _create_user(self, username, password, tenant, email):
        if self.tempest_client:
            resp, user = self.admin_client.create_user(username, password,
                                                       tenant['id'], email)
        else:
            user = self.admin_client.users.create(username, password, email,
                                                  tenant_id=tenant.id)
        return user

    def _get_user(self, tenant, username):
        if self.tempest_client:
            resp, user = self.admin_client.get_user_by_username(tenant['id'],
                                                                username)
        else:
            user = self.admin_client.users.get(username)
        return user

    def _list_roles(self):
        if self.tempest_client:
            resp, roles = self.admin_client.list_roles()
        else:
            roles = self.admin_client.roles.list()
        return roles

    def _assign_user_role(self, tenant, user, role):
        if self.tempest_client:
            self.admin_client.assign_user_role(tenant, user, role)
        else:
            self.admin_client.roles.add_user_role(user, role, tenant=tenant)

    def _delete_user(self, user):
        if self.tempest_client:
            self.admin_client.delete_user(user)
        else:
            self.admin_client.users.delete(user)

    def _delete_tenant(self, tenant):
        if self.tempest_client:
            self.admin_client.delete_tenant(tenant)
        else:
            self.admin_client.tenants.delete(tenant)

    def _create_creds(self, suffix=None, admin=False):
        rand_name_root = rand_name(self.name)
        if suffix:
            rand_name_root += suffix
        tenant_name = rand_name_root + "-tenant"
        tenant_desc = tenant_name + "-desc"
        rand_name_root = rand_name(self.name)
        tenant = self._create_tenant(name=tenant_name,
                                     description=tenant_desc)
        if suffix:
            rand_name_root += suffix
        username = rand_name_root + "-user"
        email = rand_name_root + "@example.com"
        user = self._create_user(username, self.password,
                                 tenant, email)
        if admin:
            role = None
            try:
                roles = self._list_roles()
                admin_role = self.config.identity.admin_role
                if self.tempest_client:
                    role = next(r for r in roles if r['name'] == admin_role)
                else:
                    role = next(r for r in roles if r.name == admin_role)
            except StopIteration:
                msg = "No admin role found"
                raise exceptions.NotFound(msg)
            if self.tempest_client:
                self._assign_user_role(tenant['id'], user['id'], role['id'])
            else:
                self._assign_user_role(tenant.id, user.id, role.id)
        return user, tenant

    def _get_cred_names(self, user, tenant):
        if self.tempest_client:
            username = user.get('name')
            tenant_name = tenant.get('name')
        else:
            username = user.name
            tenant_name = tenant.name
        return username, tenant_name

    def get_primary_tenant(self):
        return self.isolated_creds.get('primary')[1]

    def get_primary_user(self):
        return self.isolated_creds.get('primary')[0]

    def get_alt_tenant(self):
        return self.isolated_creds.get('alt')[1]

    def get_alt_user(self):
        return self.isolated_creds.get('alt')[0]

    def get_admin_tenant(self):
        return self.isolated_creds.get('admin')[1]

    def get_admin_user(self):
        return self.isolated_creds.get('admin')[0]

    def get_primary_creds(self):
        if self.isolated_creds.get('primary'):
            user, tenant = self.isolated_creds['primary']
            username, tenant_name = self._get_cred_names(user, tenant)
        else:
            user, tenant = self._create_creds()
            username, tenant_name = self._get_cred_names(user, tenant)
            self.isolated_creds['primary'] = (user, tenant)
            LOG.info("Aquired isolated creds:\n user: %s, tenant: %s"
                     % (username, tenant_name))
        return username, tenant_name, self.password

    def get_admin_creds(self):
        if self.isolated_creds.get('admin'):
            user, tenant = self.isolated_creds['admin']
            username, tenant_name = self._get_cred_names(user, tenant)
        else:
            user, tenant = self._create_creds(admin=True)
            username, tenant_name = self._get_cred_names(user, tenant)
            self.isolated_creds['admin'] = (user, tenant)
            LOG.info("Aquired admin isolated creds:\n user: %s, tenant: %s"
                     % (username, tenant_name))
            return username, tenant_name, self.password

    def get_alt_creds(self):
        if self.isolated_creds.get('alt'):
            user, tenant = self.isolated_creds['alt']
            username, tenant_name = self._get_cred_names(user, tenant)
        else:
            user, tenant = self._create_creds()
            username, tenant_name = self._get_cred_names(user, tenant)
            self.isolated_creds['alt'] = (user, tenant)
            LOG.info("Aquired alt isolated creds:\n user: %s, tenant: %s"
                     % (username, tenant_name))
        return username, tenant_name, self.password

    def clear_isolated_creds(self):
        if not self.isolated_creds:
            return
        for cred in self.isolated_creds:
            user, tenant = self.isolated_creds.get(cred)
            try:
                if self.tempest_client:
                    self._delete_user(user['id'])
                else:
                    self._delete_user(user.id)
            except exceptions.NotFound:
                if self.tempest_client:
                    name = user['name']
                else:
                    name = user.name
                LOG.warn("user with name: %s not found for delete" % name)
                pass
            try:
                if self.tempest_client:
                    self._delete_tenant(tenant['id'])
                else:
                    self._delete_tenant(tenant.id)
            except exceptions.NotFound:
                if self.tempest_client:
                    name = tenant['name']
                else:
                    name = tenant.name
                LOG.warn("tenant with name: %s not found for delete" % name)
                pass
