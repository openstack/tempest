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

import ipaddress

import netaddr
from oslo_log import log as logging
import six

from tempest.lib.common import cred_client
from tempest.lib.common import cred_provider
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest.lib.services import clients

LOG = logging.getLogger(__name__)


class DynamicCredentialProvider(cred_provider.CredentialProvider):
    """Creates credentials dynamically for tests

    A credential provider that, based on an initial set of
    admin credentials, creates new credentials on the fly for
    tests to use and then discard.

    :param str identity_version: identity API version to use `v2` or `v3`
    :param str admin_role: name of the admin role added to admin users
    :param str name: names of dynamic resources include this parameter
                     when specified
    :param str credentials_domain: name of the domain where the users
                                   are created. If not defined, the project
                                   domain from admin_credentials is used
    :param dict network_resources: network resources to be created for
                                   the created credentials
    :param Credentials admin_creds: initial admin credentials
    :param bool identity_admin_domain_scope: Set to true if admin should be
                                             scoped to the domain. By
                                             default this is False and the
                                             admin role is scoped to the
                                             project.
    :param str identity_admin_role: The role name to use for admin
    :param list extra_roles: A list of strings for extra roles that should
                             be assigned to all created users
    :param bool neutron_available: Whether we are running in an environemnt
                                   with neutron
    :param bool create_networks: Whether dynamic project networks should be
                                 created or not
    :param project_network_cidr: The CIDR to use for created project
                                 networks
    :param project_network_mask_bits: The network mask bits to use for
                                      created project networks
    :param public_network_id: The id for the public network to use
    :param identity_admin_endpoint_type: The endpoint type for identity
                                         admin clients. Defaults to public.
    :param identity_uri: Identity URI of the target cloud
    """

    def __init__(self, identity_version, name=None, network_resources=None,
                 credentials_domain=None, admin_role=None, admin_creds=None,
                 identity_admin_domain_scope=False,
                 identity_admin_role='admin', extra_roles=None,
                 neutron_available=False, create_networks=True,
                 project_network_cidr=None, project_network_mask_bits=None,
                 public_network_id=None, resource_prefix=None,
                 identity_admin_endpoint_type='public', identity_uri=None):
        super(DynamicCredentialProvider, self).__init__(
            identity_version=identity_version, identity_uri=identity_uri,
            admin_role=admin_role, name=name,
            credentials_domain=credentials_domain,
            network_resources=network_resources)
        self.network_resources = network_resources
        self._creds = {}
        self.ports = []
        self.resource_prefix = resource_prefix or ''
        self.neutron_available = neutron_available
        self.create_networks = create_networks
        self.project_network_cidr = project_network_cidr
        self.project_network_mask_bits = project_network_mask_bits
        self.public_network_id = public_network_id
        self.default_admin_creds = admin_creds
        self.identity_admin_domain_scope = identity_admin_domain_scope
        self.identity_admin_role = identity_admin_role or 'admin'
        self.identity_admin_endpoint_type = identity_admin_endpoint_type
        self.extra_roles = extra_roles or []
        (self.identity_admin_client,
         self.tenants_admin_client,
         self.users_admin_client,
         self.roles_admin_client,
         self.domains_admin_client,
         self.networks_admin_client,
         self.routers_admin_client,
         self.subnets_admin_client,
         self.ports_admin_client,
         self.security_groups_admin_client) = self._get_admin_clients(
            identity_admin_endpoint_type)
        # Domain where isolated credentials are provisioned (v3 only).
        # Use that of the admin account is None is configured.
        self.creds_domain_name = None
        if self.identity_version == 'v3':
            self.creds_domain_name = (
                self.default_admin_creds.project_domain_name or
                self.credentials_domain)
        self.creds_client = cred_client.get_creds_client(
            self.identity_admin_client,
            self.tenants_admin_client,
            self.users_admin_client,
            self.roles_admin_client,
            self.domains_admin_client,
            self.creds_domain_name)

    def _get_admin_clients(self, endpoint_type):
        """Returns a tuple with instances of the following admin clients

        (in this order):
            identity
            network
        """
        os = clients.ServiceClients(self.default_admin_creds,
                                    self.identity_uri)
        params = {'endpoint_type': endpoint_type}
        if self.identity_version == 'v2':
            return (os.identity_v2.IdentityClient(**params),
                    os.identity_v2.TenantsClient(**params),
                    os.identity_v2.UsersClient(**params),
                    os.identity_v2.RolesClient(**params), None,
                    os.network.NetworksClient(),
                    os.network.RoutersClient(),
                    os.network.SubnetsClient(),
                    os.network.PortsClient(),
                    os.network.SecurityGroupsClient())
        else:
            # We use a dedicated client manager for identity client in case we
            # need a different token scope for them.
            scope = 'domain' if self.identity_admin_domain_scope else 'project'
            identity_os = clients.ServiceClients(self.default_admin_creds,
                                                 self.identity_uri,
                                                 scope=scope)
            return (identity_os.identity_v3.IdentityClient(**params),
                    identity_os.identity_v3.ProjectsClient(**params),
                    identity_os.identity_v3.UsersClient(**params),
                    identity_os.identity_v3.RolesClient(**params),
                    identity_os.identity_v3.DomainsClient(**params),
                    os.network.NetworksClient(),
                    os.network.RoutersClient(),
                    os.network.SubnetsClient(),
                    os.network.PortsClient(),
                    os.network.SecurityGroupsClient())

    def _create_creds(self, admin=False, roles=None):
        """Create credentials with random name.

        Creates project and user. When admin flag is True create user
        with admin role. Assign user with additional roles (for example
        _member_) and roles requested by caller.

        :param admin: Flag if to assign to the user admin role
        :type admin: bool
        :param roles: Roles to assign for the user
        :type roles: list
        :return: Readonly Credentials with network resources
        """
        root = self.name

        project_name = data_utils.rand_name(root, prefix=self.resource_prefix)
        project_desc = project_name + "-desc"
        project = self.creds_client.create_project(
            name=project_name, description=project_desc)

        # NOTE(andreaf) User and project can be distinguished from the context,
        # having the same ID in both makes it easier to match them and debug.
        username = project_name
        user_password = data_utils.rand_password()
        email = data_utils.rand_name(
            root, prefix=self.resource_prefix) + "@example.com"
        user = self.creds_client.create_user(
            username, user_password, project, email)
        role_assigned = False
        if admin:
            self.creds_client.assign_user_role(user, project, self.admin_role)
            role_assigned = True
            if (self.identity_version == 'v3' and
                    self.identity_admin_domain_scope):
                self.creds_client.assign_user_role_on_domain(
                    user, self.identity_admin_role)
        # Add roles specified in config file
        for conf_role in self.extra_roles:
            self.creds_client.assign_user_role(user, project, conf_role)
            role_assigned = True
        # Add roles requested by caller
        if roles:
            for role in roles:
                self.creds_client.assign_user_role(user, project, role)
                role_assigned = True
        # NOTE(mtreinish) For a user to have access to a project with v3 auth
        # it must beassigned a role on the project. So we need to ensure that
        # our newly created user has a role on the newly created project.
        if self.identity_version == 'v3' and not role_assigned:
            try:
                self.creds_client.create_user_role('Member')
            except lib_exc.Conflict:
                LOG.warning('Member role already exists, ignoring conflict.')
            self.creds_client.assign_user_role(user, project, 'Member')

        creds = self.creds_client.get_credentials(user, project, user_password)
        return cred_provider.TestResources(creds)

    def _create_network_resources(self, tenant_id):
        """The function creates network resources in the given tenant.

        The function checks if network_resources class member is empty,
        In case it is, it will create a network, a subnet and a router for
        the tenant according to the given tenant id parameter.
        Otherwise it will create a network resource according
        to the values from network_resources dict.

        :param tenant_id: The tenant id to create resources for.
        :type tenant_id: str
        :raises: InvalidConfiguration, Exception
        :returns: network resources(network,subnet,router)
        :rtype: tuple
        """
        network = None
        subnet = None
        router = None
        # Make sure settings
        if self.network_resources:
            if self.network_resources['router']:
                if (not self.network_resources['subnet'] or
                    not self.network_resources['network']):
                    raise lib_exc.InvalidConfiguration(
                        'A router requires a subnet and network')
            elif self.network_resources['subnet']:
                if not self.network_resources['network']:
                    raise lib_exc.InvalidConfiguration(
                        'A subnet requires a network')
            elif self.network_resources['dhcp']:
                raise lib_exc.InvalidConfiguration('DHCP requires a subnet')

        rand_name_root = data_utils.rand_name(
            self.name, prefix=self.resource_prefix)
        if not self.network_resources or self.network_resources['network']:
            network_name = rand_name_root + "-network"
            network = self._create_network(network_name, tenant_id)
        try:
            if not self.network_resources or self.network_resources['subnet']:
                subnet_name = rand_name_root + "-subnet"
                subnet = self._create_subnet(subnet_name, tenant_id,
                                             network['id'])
            if not self.network_resources or self.network_resources['router']:
                router_name = rand_name_root + "-router"
                router = self._create_router(router_name, tenant_id)
                self._add_router_interface(router['id'], subnet['id'])
        except Exception:
            try:
                if router:
                    self._clear_isolated_router(router['id'], router['name'])
                if subnet:
                    self._clear_isolated_subnet(subnet['id'], subnet['name'])
                if network:
                    self._clear_isolated_network(network['id'],
                                                 network['name'])
            except Exception as cleanup_exception:
                msg = "There was an exception trying to setup network " \
                      "resources for tenant %s, and this error happened " \
                      "trying to clean them up: %s"
                LOG.warning(msg, tenant_id, cleanup_exception)
            raise
        return network, subnet, router

    def _create_network(self, name, tenant_id):
        resp_body = self.networks_admin_client.create_network(
            name=name, tenant_id=tenant_id)
        return resp_body['network']

    def _create_subnet(self, subnet_name, tenant_id, network_id):
        base_cidr = netaddr.IPNetwork(self.project_network_cidr)
        mask_bits = self.project_network_mask_bits
        for subnet_cidr in base_cidr.subnet(mask_bits):
            try:
                if self.network_resources:
                    resp_body = self.subnets_admin_client.\
                        create_subnet(
                            network_id=network_id, cidr=str(subnet_cidr),
                            name=subnet_name,
                            tenant_id=tenant_id,
                            enable_dhcp=self.network_resources['dhcp'],
                            ip_version=(ipaddress.ip_network(
                                six.text_type(subnet_cidr)).version))
                else:
                    resp_body = self.subnets_admin_client.\
                        create_subnet(network_id=network_id,
                                      cidr=str(subnet_cidr),
                                      name=subnet_name,
                                      tenant_id=tenant_id,
                                      ip_version=(ipaddress.ip_network(
                                          six.text_type(subnet_cidr)).version))
                break
            except lib_exc.BadRequest as e:
                if 'overlaps with another subnet' not in str(e):
                    raise
        else:
            message = 'Available CIDR for subnet creation could not be found'
            raise Exception(message)
        return resp_body['subnet']

    def _create_router(self, router_name, tenant_id):
        kwargs = {'name': router_name,
                  'tenant_id': tenant_id}
        if self.public_network_id:
            kwargs['external_gateway_info'] = dict(
                network_id=self.public_network_id)
        resp_body = self.routers_admin_client.create_router(**kwargs)
        return resp_body['router']

    def _add_router_interface(self, router_id, subnet_id):
        self.routers_admin_client.add_router_interface(router_id,
                                                       subnet_id=subnet_id)

    def get_credentials(self, credential_type):
        if self._creds.get(str(credential_type)):
            credentials = self._creds[str(credential_type)]
        else:
            if credential_type in ['primary', 'alt', 'admin']:
                is_admin = (credential_type == 'admin')
                credentials = self._create_creds(admin=is_admin)
            else:
                credentials = self._create_creds(roles=credential_type)
            self._creds[str(credential_type)] = credentials
            # Maintained until tests are ported
            LOG.info("Acquired dynamic creds:\n"
                     " credentials: %s", credentials)
            if (self.neutron_available and self.create_networks):
                network, subnet, router = self._create_network_resources(
                    credentials.tenant_id)
                credentials.set_resources(network=network, subnet=subnet,
                                          router=router)
                LOG.info("Created isolated network resources for:\n"
                         " credentials: %s", credentials)
        return credentials

    def get_primary_creds(self):
        return self.get_credentials('primary')

    def get_admin_creds(self):
        return self.get_credentials('admin')

    def get_alt_creds(self):
        return self.get_credentials('alt')

    def get_creds_by_roles(self, roles, force_new=False):
        roles = list(set(roles))
        # The roles list as a str will become the index as the dict key for
        # the created credentials set in the dynamic_creds dict.
        exist_creds = self._creds.get(str(roles))
        # If force_new flag is True 2 cred sets with the same roles are needed
        # handle this by creating a separate index for old one to store it
        # separately for cleanup
        if exist_creds and force_new:
            new_index = str(roles) + '-' + str(len(self._creds))
            self._creds[new_index] = exist_creds
            del self._creds[str(roles)]
        return self.get_credentials(roles)

    def _clear_isolated_router(self, router_id, router_name):
        client = self.routers_admin_client
        try:
            client.delete_router(router_id)
        except lib_exc.NotFound:
            LOG.warning('router with name: %s not found for delete',
                        router_name)

    def _clear_isolated_subnet(self, subnet_id, subnet_name):
        client = self.subnets_admin_client
        try:
            client.delete_subnet(subnet_id)
        except lib_exc.NotFound:
            LOG.warning('subnet with name: %s not found for delete',
                        subnet_name)

    def _clear_isolated_network(self, network_id, network_name):
        net_client = self.networks_admin_client
        try:
            net_client.delete_network(network_id)
        except lib_exc.NotFound:
            LOG.warning('network with name: %s not found for delete',
                        network_name)

    def _cleanup_default_secgroup(self, tenant):
        nsg_client = self.security_groups_admin_client
        resp_body = nsg_client.list_security_groups(tenant_id=tenant,
                                                    name="default")
        secgroups_to_delete = resp_body['security_groups']
        for secgroup in secgroups_to_delete:
            try:
                nsg_client.delete_security_group(secgroup['id'])
            except lib_exc.NotFound:
                LOG.warning('Security group %s, id %s not found for clean-up',
                            secgroup['name'], secgroup['id'])

    def _clear_isolated_net_resources(self):
        client = self.routers_admin_client
        for cred in self._creds:
            creds = self._creds.get(cred)
            if (not creds or not any([creds.router, creds.network,
                                      creds.subnet])):
                continue
            LOG.debug("Clearing network: %(network)s, "
                      "subnet: %(subnet)s, router: %(router)s",
                      {'network': creds.network, 'subnet': creds.subnet,
                       'router': creds.router})
            if (not self.network_resources or
                    (self.network_resources.get('router') and creds.subnet)):
                try:
                    client.remove_router_interface(
                        creds.router['id'],
                        subnet_id=creds.subnet['id'])
                except lib_exc.NotFound:
                    LOG.warning('router with name: %s not found for delete',
                                creds.router['name'])
                self._clear_isolated_router(creds.router['id'],
                                            creds.router['name'])
            if (not self.network_resources or
                self.network_resources.get('subnet')):
                self._clear_isolated_subnet(creds.subnet['id'],
                                            creds.subnet['name'])
            if (not self.network_resources or
                self.network_resources.get('network')):
                self._clear_isolated_network(creds.network['id'],
                                             creds.network['name'])

    def clear_creds(self):
        if not self._creds:
            return
        self._clear_isolated_net_resources()
        for creds in six.itervalues(self._creds):
            try:
                self.creds_client.delete_user(creds.user_id)
            except lib_exc.NotFound:
                LOG.warning("user with name: %s not found for delete",
                            creds.username)
            # NOTE(zhufl): Only when neutron's security_group ext is
            # enabled, _cleanup_default_secgroup will not raise error. But
            # here cannot use test_utils.is_extension_enabled for it will cause
            # "circular dependency". So here just use try...except to
            # ensure tenant deletion without big changes.
            try:
                if self.neutron_available:
                    self._cleanup_default_secgroup(creds.tenant_id)
            except lib_exc.NotFound:
                LOG.warning("failed to cleanup tenant %s's secgroup",
                            creds.tenant_name)
            try:
                self.creds_client.delete_project(creds.tenant_id)
            except lib_exc.NotFound:
                LOG.warning("tenant with name: %s not found for delete",
                            creds.tenant_name)
        self._creds = {}

    def is_multi_user(self):
        return True

    def is_multi_tenant(self):
        return True

    def is_role_available(self, role):
        return True
