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

import netaddr

import keystoneclient.v2_0.client as keystoneclient
import neutronclient.v2_0.client as neutronclient

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
        self.isolated_net_resources = {}
        self.ports = []
        self.name = name
        self.config = config.TempestConfig()
        self.tempest_client = tempest_client
        self.interface = interface
        self.password = password
        self.identity_admin_client, self.network_admin_client = (
            self._get_admin_clients())

    def _get_official_admin_clients(self):
        username = self.config.identity.admin_username
        password = self.config.identity.admin_password
        tenant_name = self.config.identity.admin_tenant_name
        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation
        identity_client = keystoneclient.Client(username=username,
                                                password=password,
                                                tenant_name=tenant_name,
                                                auth_url=auth_url,
                                                insecure=dscv)
        network_client = neutronclient.Client(username=username,
                                              password=password,
                                              tenant_name=tenant_name,
                                              auth_url=auth_url,
                                              insecure=dscv)
        return identity_client, network_client

    def _get_admin_clients(self):
        """
        Returns a tuple with instances of the following admin clients (in this
        order):
            identity
            network
        """
        if self.tempest_client:
            os = clients.AdminManager(interface=self.interface)
            admin_clients = (os.identity_client,
                             os.network_client,)
        else:
            admin_clients = self._get_official_admin_clients()
        return admin_clients

    def _create_tenant(self, name, description):
        if self.tempest_client:
            resp, tenant = self.identity_admin_client.create_tenant(
                name=name, description=description)
        else:
            tenant = self.identity_admin_client.tenants.create(
                name,
                description=description)
        return tenant

    def _get_tenant_by_name(self, name):
        if self.tempest_client:
            resp, tenant = self.identity_admin_client.get_tenant_by_name(name)
        else:
            tenants = self.identity_admin_client.tenants.list()
            for ten in tenants:
                if ten['name'] == name:
                    tenant = ten
                    break
            else:
                raise exceptions.NotFound('No such tenant')
        return tenant

    def _create_user(self, username, password, tenant, email):
        if self.tempest_client:
            resp, user = self.identity_admin_client.create_user(username,
                                                                password,
                                                                tenant['id'],
                                                                email)
        else:
            user = self.identity_admin_client.users.create(username, password,
                                                           email,
                                                           tenant_id=tenant.id)
        return user

    def _get_user(self, tenant, username):
        if self.tempest_client:
            resp, user = self.identity_admin_client.get_user_by_username(
                tenant['id'],
                username)
        else:
            user = self.identity_admin_client.users.get(username)
        return user

    def _list_roles(self):
        if self.tempest_client:
            resp, roles = self.identity_admin_client.list_roles()
        else:
            roles = self.identity_admin_client.roles.list()
        return roles

    def _assign_user_role(self, tenant, user, role):
        if self.tempest_client:
            self.identity_admin_client.assign_user_role(tenant, user, role)
        else:
            self.identity_admin_client.roles.add_user_role(user,
                                                           role, tenant=tenant)

    def _delete_user(self, user):
        if self.tempest_client:
            self.identity_admin_client.delete_user(user)
        else:
            self.identity_admin_client.users.delete(user)

    def _delete_tenant(self, tenant):
        if self.tempest_client:
            self.identity_admin_client.delete_tenant(tenant)
        else:
            self.identity_admin_client.tenants.delete(tenant)

    def _create_creds(self, suffix=None, admin=False):
        rand_name_root = rand_name(self.name)
        if suffix:
            rand_name_root += suffix
        tenant_name = rand_name_root + "-tenant"
        tenant_desc = tenant_name + "-desc"
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

    def _get_tenant_id(self, tenant):
        if self.tempest_client:
            return tenant.get('id')
        else:
            return tenant.id

    def _create_network_resources(self, tenant_id):
        network = None
        subnet = None
        router = None
        rand_name_root = rand_name(self.name)
        network_name = rand_name_root + "-network"
        network = self._create_network(network_name, tenant_id)
        try:
            subnet_name = rand_name_root + "-subnet"
            subnet = self._create_subnet(subnet_name, tenant_id, network['id'])
            router_name = rand_name_root + "-router"
            router = self._create_router(router_name, tenant_id)
            self._add_router_interface(router['id'], subnet['id'])
        except Exception:
            if router:
                self._clear_isolated_router(router['id'], router['name'])
            if subnet:
                self._clear_isolated_subnet(subnet['id'], subnet['name'])
            if network:
                self._clear_isolated_network(network['id'], network['name'])
            raise
        return network, subnet, router

    def _create_network(self, name, tenant_id):
        if self.tempest_client:
            resp, resp_body = self.network_admin_client.create_network(
                name, tenant_id=tenant_id)
        else:
            body = {'network': {'tenant_id': tenant_id, 'name': name}}
            resp_body = self.network_admin_client.create_network(body)
        return resp_body['network']

    def _create_subnet(self, subnet_name, tenant_id, network_id):
        if not self.tempest_client:
            body = {'subnet': {'name': subnet_name, 'tenant_id': tenant_id,
                               'network_id': network_id, 'ip_version': 4}}
        base_cidr = netaddr.IPNetwork(self.config.network.tenant_network_cidr)
        mask_bits = self.config.network.tenant_network_mask_bits
        for subnet_cidr in base_cidr.subnet(mask_bits):
            try:
                if self.tempest_client:
                    resp, resp_body = self.network_admin_client.create_subnet(
                        network_id, str(subnet_cidr), name=subnet_name,
                        tenant_id=tenant_id)
                else:
                    body['subnet']['cidr'] = str(subnet_cidr)
                    resp_body = self.network_admin_client.create_subnet(body)
                break
            except exceptions.BadRequest as e:
                if 'overlaps with another subnet' not in str(e):
                    raise
        else:
            e = exceptions.BuildErrorException()
            e.message = 'Available CIDR for subnet creation could not be found'
            raise e
        return resp_body['subnet']

    def _create_router(self, router_name, tenant_id):
        external_net_id = dict(
            network_id=self.config.network.public_network_id)
        if self.tempest_client:
            resp, resp_body = self.network_admin_client.create_router(
                router_name,
                external_gateway_info=external_net_id,
                tenant_id=tenant_id)
        else:
            body = {'router': {'name': router_name, 'tenant_id': tenant_id,
                               'external_gateway_info': external_net_id,
                               'admin_state_up': True}}
            resp_body = self.network_admin_client.create_router(body)
        return resp_body['router']

    def _add_router_interface(self, router_id, subnet_id):
        if self.tempest_client:
            self.network_admin_client.add_router_interface_with_subnet_id(
                router_id, subnet_id)
        else:
            body = {'subnet_id': subnet_id}
            self.network_admin_client.add_interface_router(router_id, body)

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

    def get_primary_network(self):
        return self.isolated_net_resources.get('primary')[0]

    def get_primary_subnet(self):
        return self.isolated_net_resources.get('primary')[1]

    def get_primary_router(self):
        return self.isolated_net_resources.get('primary')[2]

    def get_admin_network(self):
        return self.isolated_net_resources.get('admin')[0]

    def get_admin_subnet(self):
        return self.isolated_net_resources.get('admin')[1]

    def get_admin_router(self):
        return self.isolated_net_resources.get('admin')[2]

    def get_alt_network(self):
        return self.isolated_net_resources.get('alt')[0]

    def get_alt_subnet(self):
        return self.isolated_net_resources.get('alt')[1]

    def get_alt_router(self):
        return self.isolated_net_resources.get('alt')[2]

    def get_primary_creds(self):
        if self.isolated_creds.get('primary'):
            user, tenant = self.isolated_creds['primary']
            username, tenant_name = self._get_cred_names(user, tenant)
        else:
            user, tenant = self._create_creds()
            username, tenant_name = self._get_cred_names(user, tenant)
            self.isolated_creds['primary'] = (user, tenant)
            LOG.info("Acquired isolated creds:\n user: %s, tenant: %s"
                     % (username, tenant_name))
            if self.config.service_available.neutron:
                network, subnet, router = self._create_network_resources(
                    self._get_tenant_id(tenant))
                self.isolated_net_resources['primary'] = (
                    network, subnet, router,)
                LOG.info("Created isolated network resources for : \n"
                         + " user: %s, tenant: %s" % (username, tenant_name))
        return username, tenant_name, self.password

    def get_admin_creds(self):
        if self.isolated_creds.get('admin'):
            user, tenant = self.isolated_creds['admin']
            username, tenant_name = self._get_cred_names(user, tenant)
        else:
            user, tenant = self._create_creds(admin=True)
            username, tenant_name = self._get_cred_names(user, tenant)
            self.isolated_creds['admin'] = (user, tenant)
            LOG.info("Acquired admin isolated creds:\n user: %s, tenant: %s"
                     % (username, tenant_name))
            if self.config.service_available.neutron:
                network, subnet, router = self._create_network_resources(
                    self._get_tenant_id(tenant))
                self.isolated_net_resources['admin'] = (
                    network, subnet, router,)
                LOG.info("Created isolated network resources for : \n"
                         + " user: %s, tenant: %s" % (username, tenant_name))
        return username, tenant_name, self.password

    def get_alt_creds(self):
        if self.isolated_creds.get('alt'):
            user, tenant = self.isolated_creds['alt']
            username, tenant_name = self._get_cred_names(user, tenant)
        else:
            user, tenant = self._create_creds()
            username, tenant_name = self._get_cred_names(user, tenant)
            self.isolated_creds['alt'] = (user, tenant)
            LOG.info("Acquired alt isolated creds:\n user: %s, tenant: %s"
                     % (username, tenant_name))
            if self.config.service_available.neutron:
                network, subnet, router = self._create_network_resources(
                    self._get_tenant_id(tenant))
                self.isolated_net_resources['alt'] = (
                    network, subnet, router,)
                LOG.info("Created isolated network resources for : \n"
                         + " user: %s, tenant: %s" % (username, tenant_name))
        return username, tenant_name, self.password

    def _clear_isolated_router(self, router_id, router_name):
        net_client = self.network_admin_client
        try:
            net_client.delete_router(router_id)
        except exceptions.NotFound:
            LOG.warn('router with name: %s not found for delete' %
                     router_name)
            pass

    def _clear_isolated_subnet(self, subnet_id, subnet_name):
        net_client = self.network_admin_client
        try:
            net_client.delete_subnet(subnet_id)
        except exceptions.NotFound:
            LOG.warn('subnet with name: %s not found for delete' %
                     subnet_name)
            pass

    def _clear_isolated_network(self, network_id, network_name):
        net_client = self.network_admin_client
        try:
            net_client.delete_network(network_id)
        except exceptions.NotFound:
            LOG.warn('network with name: %s not found for delete' %
                     network_name)
            pass

    def _cleanup_ports(self, network_id):
        # TODO(mlavalle) This method will be removed once patch
        # https://review.openstack.org/#/c/46563/ merges in Neutron
        if not self.ports:
            if self.tempest_client:
                resp, resp_body = self.network_admin_client.list_ports()
            else:
                resp_body = self.network_admin_client.list_ports()
            self.ports = resp_body['ports']
        ports_to_delete = [
            port for port in self.ports if port['network_id'] == network_id]
        for port in ports_to_delete:
            try:
                LOG.info('Cleaning up port id %s, name %s' %
                         (port['id'], port['name']))
                self.network_admin_client.delete_port(port['id'])
            except exceptions.NotFound:
                LOG.warn('Port id: %s, name %s not found for clean-up' %
                         (port['id'], port['name']))

    def _clear_isolated_net_resources(self):
        net_client = self.network_admin_client
        for cred in self.isolated_net_resources:
            network, subnet, router = self.isolated_net_resources.get(cred)
            try:
                if self.tempest_client:
                    net_client.remove_router_interface_with_subnet_id(
                        router['id'], subnet['id'])
                else:
                    body = {'subnet_id': subnet['id']}
                    net_client.remove_interface_router(router['id'], body)
            except exceptions.NotFound:
                LOG.warn('router with name: %s not found for delete' %
                         router['name'])
                pass
            self._clear_isolated_router(router['id'], router['name'])
            # TODO(mlavalle) This method call will be removed once patch
            # https://review.openstack.org/#/c/46563/ merges in Neutron
            self._cleanup_ports(network['id'])
            self._clear_isolated_subnet(subnet['id'], subnet['name'])
            self._clear_isolated_network(network['id'], network['name'])
            LOG.info("Cleared isolated network resources: \n"
                     + " network: %s, subnet: %s, router: %s"
                     % (network['name'], subnet['name'], router['name']))

    def clear_isolated_creds(self):
        if not self.isolated_creds:
            return
        self._clear_isolated_net_resources()
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
