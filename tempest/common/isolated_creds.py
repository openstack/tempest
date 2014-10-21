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

from tempest import auth
from tempest import clients
from tempest.common import cred_provider
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging

CONF = config.CONF
LOG = logging.getLogger(__name__)


class IsolatedCreds(cred_provider.CredentialProvider):

    def __init__(self, name, interface='json', password='pass',
                 network_resources=None):
        super(IsolatedCreds, self).__init__(name, interface, password,
                                            network_resources)
        self.network_resources = network_resources
        self.isolated_creds = {}
        self.isolated_net_resources = {}
        self.ports = []
        self.interface = interface
        self.password = password
        self.identity_admin_client, self.network_admin_client = (
            self._get_admin_clients())

    def _get_admin_clients(self):
        """
        Returns a tuple with instances of the following admin clients (in this
        order):
            identity
            network
        """
        os = clients.AdminManager(interface=self.interface)
        return os.identity_client, os.network_client

    def _create_tenant(self, name, description):
        _, tenant = self.identity_admin_client.create_tenant(
            name=name, description=description)
        return tenant

    def _get_tenant_by_name(self, name):
        _, tenant = self.identity_admin_client.get_tenant_by_name(name)
        return tenant

    def _create_user(self, username, password, tenant, email):
        _, user = self.identity_admin_client.create_user(
            username, password, tenant['id'], email)
        return user

    def _get_user(self, tenant, username):
        _, user = self.identity_admin_client.get_user_by_username(
            tenant['id'], username)
        return user

    def _list_roles(self):
        _, roles = self.identity_admin_client.list_roles()
        return roles

    def _assign_user_role(self, tenant, user, role_name):
        role = None
        try:
            roles = self._list_roles()
            role = next(r for r in roles if r['name'] == role_name)
        except StopIteration:
            msg = 'No "%s" role found' % role_name
            raise exceptions.NotFound(msg)
        self.identity_admin_client.assign_user_role(tenant['id'], user['id'],
                                                    role['id'])

    def _delete_user(self, user):
        self.identity_admin_client.delete_user(user)

    def _delete_tenant(self, tenant):
        if CONF.service_available.neutron:
            self._cleanup_default_secgroup(tenant)
        self.identity_admin_client.delete_tenant(tenant)

    def _create_creds(self, suffix="", admin=False):
        """Create random credentials under the following schema.

        If the name contains a '.' is the full class path of something, and
        we don't really care. If it isn't, it's probably a meaningful name,
        so use it.

        For logging purposes, -user and -tenant are long and redundant,
        don't use them. The user# will be sufficient to figure it out.
        """
        if '.' in self.name:
            root = ""
        else:
            root = self.name

        tenant_name = data_utils.rand_name(root) + suffix
        tenant_desc = tenant_name + "-desc"
        tenant = self._create_tenant(name=tenant_name,
                                     description=tenant_desc)

        username = data_utils.rand_name(root) + suffix
        email = data_utils.rand_name(root) + suffix + "@example.com"
        user = self._create_user(username, self.password,
                                 tenant, email)
        if CONF.service_available.swift:
            # NOTE(andrey-mp): user needs this role to create containers
            # in swift
            swift_operator_role = CONF.object_storage.operator_role
            self._assign_user_role(tenant, user, swift_operator_role)
        if admin:
            self._assign_user_role(tenant, user, CONF.identity.admin_role)
        return self._get_credentials(user, tenant)

    def _get_credentials(self, user, tenant):
        return auth.get_credentials(
            username=user['name'], user_id=user['id'],
            tenant_name=tenant['name'], tenant_id=tenant['id'],
            password=self.password)

    def _create_network_resources(self, tenant_id):
        network = None
        subnet = None
        router = None
        # Make sure settings
        if self.network_resources:
            if self.network_resources['router']:
                if (not self.network_resources['subnet'] or
                    not self.network_resources['network']):
                    raise exceptions.InvalidConfiguration(
                        'A router requires a subnet and network')
            elif self.network_resources['subnet']:
                if not self.network_resources['network']:
                    raise exceptions.InvalidConfiguration(
                        'A subnet requires a network')
            elif self.network_resources['dhcp']:
                raise exceptions.InvalidConfiguration('DHCP requires a subnet')

        data_utils.rand_name_root = data_utils.rand_name(self.name)
        if not self.network_resources or self.network_resources['network']:
            network_name = data_utils.rand_name_root + "-network"
            network = self._create_network(network_name, tenant_id)
        try:
            if not self.network_resources or self.network_resources['subnet']:
                subnet_name = data_utils.rand_name_root + "-subnet"
                subnet = self._create_subnet(subnet_name, tenant_id,
                                             network['id'])
            if not self.network_resources or self.network_resources['router']:
                router_name = data_utils.rand_name_root + "-router"
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
        _, resp_body = self.network_admin_client.create_network(
            name=name, tenant_id=tenant_id)
        return resp_body['network']

    def _create_subnet(self, subnet_name, tenant_id, network_id):
        base_cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        mask_bits = CONF.network.tenant_network_mask_bits
        for subnet_cidr in base_cidr.subnet(mask_bits):
            try:
                if self.network_resources:
                    _, resp_body = self.network_admin_client.\
                        create_subnet(
                            network_id=network_id, cidr=str(subnet_cidr),
                            name=subnet_name,
                            tenant_id=tenant_id,
                            enable_dhcp=self.network_resources['dhcp'],
                            ip_version=4)
                else:
                    _, resp_body = self.network_admin_client.\
                        create_subnet(network_id=network_id,
                                      cidr=str(subnet_cidr),
                                      name=subnet_name,
                                      tenant_id=tenant_id,
                                      ip_version=4)
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
            network_id=CONF.network.public_network_id)
        _, resp_body = self.network_admin_client.create_router(
            router_name,
            external_gateway_info=external_net_id,
            tenant_id=tenant_id)
        return resp_body['router']

    def _add_router_interface(self, router_id, subnet_id):
        self.network_admin_client.add_router_interface_with_subnet_id(
            router_id, subnet_id)

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

    def get_credentials(self, credential_type):
        if self.isolated_creds.get(credential_type):
            credentials = self.isolated_creds[credential_type]
        else:
            is_admin = (credential_type == 'admin')
            credentials = self._create_creds(admin=is_admin)
            self.isolated_creds[credential_type] = credentials
            # Maintained until tests are ported
            LOG.info("Acquired isolated creds:\n credentials: %s"
                     % credentials)
            if (CONF.service_available.neutron and
                not CONF.baremetal.driver_enabled):
                network, subnet, router = self._create_network_resources(
                    credentials.tenant_id)
                self.isolated_net_resources[credential_type] = (
                    network, subnet, router,)
                LOG.info("Created isolated network resources for : \n"
                         + " credentials: %s" % credentials)
        return credentials

    def get_primary_creds(self):
        return self.get_credentials('primary')

    def get_admin_creds(self):
        return self.get_credentials('admin')

    def get_alt_creds(self):
        return self.get_credentials('alt')

    def _clear_isolated_router(self, router_id, router_name):
        net_client = self.network_admin_client
        try:
            net_client.delete_router(router_id)
        except exceptions.NotFound:
            LOG.warn('router with name: %s not found for delete' %
                     router_name)

    def _clear_isolated_subnet(self, subnet_id, subnet_name):
        net_client = self.network_admin_client
        try:
            net_client.delete_subnet(subnet_id)
        except exceptions.NotFound:
            LOG.warn('subnet with name: %s not found for delete' %
                     subnet_name)

    def _clear_isolated_network(self, network_id, network_name):
        net_client = self.network_admin_client
        try:
            net_client.delete_network(network_id)
        except exceptions.NotFound:
            LOG.warn('network with name: %s not found for delete' %
                     network_name)

    def _cleanup_default_secgroup(self, tenant):
        net_client = self.network_admin_client
        _, resp_body = net_client.list_security_groups(tenant_id=tenant,
                                                       name="default")
        secgroups_to_delete = resp_body['security_groups']
        for secgroup in secgroups_to_delete:
            try:
                net_client.delete_security_group(secgroup['id'])
            except exceptions.NotFound:
                LOG.warn('Security group %s, id %s not found for clean-up' %
                         (secgroup['name'], secgroup['id']))

    def _clear_isolated_net_resources(self):
        net_client = self.network_admin_client
        for cred in self.isolated_net_resources:
            network, subnet, router = self.isolated_net_resources.get(cred)
            LOG.debug("Clearing network: %(network)s, "
                      "subnet: %(subnet)s, router: %(router)s",
                      {'network': network, 'subnet': subnet, 'router': router})
            if (not self.network_resources or
                self.network_resources.get('router')):
                try:
                    net_client.remove_router_interface_with_subnet_id(
                        router['id'], subnet['id'])
                except exceptions.NotFound:
                    LOG.warn('router with name: %s not found for delete' %
                             router['name'])
                self._clear_isolated_router(router['id'], router['name'])
            if (not self.network_resources or
                self.network_resources.get('subnet')):
                self._clear_isolated_subnet(subnet['id'], subnet['name'])
            if (not self.network_resources or
                self.network_resources.get('network')):
                self._clear_isolated_network(network['id'], network['name'])

    def clear_isolated_creds(self):
        if not self.isolated_creds:
            return
        self._clear_isolated_net_resources()
        for creds in self.isolated_creds.itervalues():
            try:
                self._delete_user(creds.user_id)
            except exceptions.NotFound:
                LOG.warn("user with name: %s not found for delete" %
                         creds.username)
            try:
                self._delete_tenant(creds.tenant_id)
            except exceptions.NotFound:
                LOG.warn("tenant with name: %s not found for delete" %
                         creds.tenant_name)

    def is_multi_user(self):
        return True

    def is_multi_tenant(self):
        return True
