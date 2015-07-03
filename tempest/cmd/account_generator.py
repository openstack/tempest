#!/usr/bin/env python

# Copyright 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Utility for creating **accounts.yaml** file for concurrent test runs.
Creates one primary user, one alt user, one swift admin, one stack owner
and one admin (optionally) for each concurrent thread. The utility creates
user for each tenant. The **accounts.yaml** file will be valid and contain
credentials for created users, so each user will be in separate tenant and
have the username, tenant_name, password and roles.

**Usage:** ``tempest-account-generator [-h] [OPTIONS] accounts_file.yaml``.

Positional Arguments
-----------------
**accounts_file.yaml** (Required) Provide an output accounts yaml file. Utility
creates a .yaml file in the directory where the command is ran. The appropriate
name for the file is *accounts.yaml* and it should be placed in *tempest/etc*
directory.

Authentication
--------------

Account generator creates users and tenants so it needs the admin credentials
of your cloud to operate properly. The corresponding info can be given either
through CLI options or environment variables.

You're probably familiar with these, but just to remind::

    +----------+------------------+----------------------+
    | Param    | CLI              | Environment Variable |
    +----------+------------------+----------------------+
    | Username | --os-username    | OS_USERNAME          |
    | Password | --os-password    | OS_PASSWORD          |
    | Tenant   | --os-tenant-name | OS_TENANT_NAME       |
    +----------+------------------+----------------------+

Optional Arguments
-----------------
**-h**, **--help** (Optional) Shows help message with the description of
utility and its arguments, and exits.

**c /etc/tempest.conf**, **--config-file /etc/tempest.conf** (Optional) Path to
tempest config file.

**--os-username <auth-user-name>** (Optional) Name used for authentication with
the OpenStack Identity service. Defaults to env[OS_USERNAME]. Note: User should
have permissions to create new user accounts and tenants.

**--os-password <auth-password>** (Optional) Password used for authentication
with the OpenStack Identity service. Defaults to env[OS_PASSWORD].

**--os-tenant-name <auth-tenant-name>** (Optional) Tenant to request
authorization on. Defaults to env[OS_TENANT_NAME].

**--tag TAG** (Optional) Resources tag. Each created resource (user, project)
will have the prefix with the given TAG in its name. Using tag is recommended
for the further using, cleaning resources.

**-r CONCURRENCY**, **--concurrency CONCURRENCY** (Required) Concurrency count
(default: 1). The number of accounts required can be estimated as
CONCURRENCY x 2. Each user provided in *accounts.yaml* file will be in
a different tenant. This is required to provide isolation between test for
running in parallel.

**--with-admin** (Optional) Creates admin for each concurrent group
(default: False).

To see help on specific argument, please do: ``tempest-account-generator
[OPTIONS] <accounts_file.yaml> -h``.
"""
import argparse
import netaddr
import os

from oslo_log import log as logging
import yaml

from tempest import config
from tempest import exceptions
from tempest.services.identity.v2.json import identity_client
from tempest.services.network.json import network_client
import tempest_lib.auth
from tempest_lib.common.utils import data_utils
import tempest_lib.exceptions

LOG = None
CONF = config.CONF


def setup_logging():
    global LOG
    logging.setup(CONF, __name__)
    LOG = logging.getLogger(__name__)


def get_admin_clients(opts):
    _creds = tempest_lib.auth.KeystoneV2Credentials(
        username=opts.os_username,
        password=opts.os_password,
        tenant_name=opts.os_tenant_name)
    auth_params = {
        'disable_ssl_certificate_validation':
            CONF.identity.disable_ssl_certificate_validation,
        'ca_certs': CONF.identity.ca_certificates_file,
        'trace_requests': CONF.debug.trace_requests
    }
    _auth = tempest_lib.auth.KeystoneV2AuthProvider(
        _creds, CONF.identity.uri, **auth_params)
    params = {
        'disable_ssl_certificate_validation':
            CONF.identity.disable_ssl_certificate_validation,
        'ca_certs': CONF.identity.ca_certificates_file,
        'trace_requests': CONF.debug.trace_requests,
        'build_interval': CONF.compute.build_interval,
        'build_timeout': CONF.compute.build_timeout
    }
    identity_admin = identity_client.IdentityClientJSON(
        _auth,
        CONF.identity.catalog_type,
        CONF.identity.region,
        endpoint_type='adminURL',
        **params
    )
    network_admin = None
    if (CONF.service_available.neutron and
        CONF.auth.create_isolated_networks):
        network_admin = network_client.NetworkClientJSON(
            _auth,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type='adminURL',
            **params)
    return identity_admin, network_admin


def create_resources(opts, resources):
    identity_admin, network_admin = get_admin_clients(opts)
    roles = identity_admin.list_roles()
    for u in resources['users']:
        u['role_ids'] = []
        for r in u.get('roles', ()):
            try:
                role = filter(lambda r_: r_['name'] == r, roles)[0]
                u['role_ids'] += [role['id']]
            except IndexError:
                raise exceptions.TempestException(
                    "Role: %s - doesn't exist" % r
                )
    existing = [x['name'] for x in identity_admin.list_tenants()]
    for tenant in resources['tenants']:
        if tenant not in existing:
            identity_admin.create_tenant(tenant)
        else:
            LOG.warn("Tenant '%s' already exists in this environment" % tenant)
    LOG.info('Tenants created')
    for u in resources['users']:
        try:
            tenant = identity_admin.get_tenant_by_name(u['tenant'])
        except tempest_lib.exceptions.NotFound:
            LOG.error("Tenant: %s - not found" % u['tenant'])
            continue
        while True:
            try:
                identity_admin.get_user_by_username(tenant['id'], u['name'])
            except tempest_lib.exceptions.NotFound:
                identity_admin.create_user(
                    u['name'], u['pass'], tenant['id'],
                    "%s@%s" % (u['name'], tenant['id']),
                    enabled=True)
                break
            else:
                LOG.warn("User '%s' already exists in this environment. "
                         "New name generated" % u['name'])
                u['name'] = random_user_name(opts.tag, u['prefix'])

    LOG.info('Users created')
    if network_admin:
        for u in resources['users']:
            tenant = identity_admin.get_tenant_by_name(u['tenant'])
            network_name, router_name = create_network_resources(network_admin,
                                                                 tenant['id'],
                                                                 u['name'])
            u['network'] = network_name
            u['router'] = router_name
        LOG.info('Networks created')
    for u in resources['users']:
        try:
            tenant = identity_admin.get_tenant_by_name(u['tenant'])
        except tempest_lib.exceptions.NotFound:
            LOG.error("Tenant: %s - not found" % u['tenant'])
            continue
        try:
            user = identity_admin.get_user_by_username(tenant['id'],
                                                       u['name'])
        except tempest_lib.exceptions.NotFound:
            LOG.error("User: %s - not found" % u['user'])
            continue
        for r in u['role_ids']:
            try:
                identity_admin.assign_user_role(tenant['id'], user['id'], r)
            except tempest_lib.exceptions.Conflict:
                # don't care if it's already assigned
                pass
    LOG.info('Roles assigned')
    LOG.info('Resources deployed successfully!')


def create_network_resources(network_admin_client, tenant_id, name):

    def _create_network(name):
        resp_body = network_admin_client.create_network(
            name=name, tenant_id=tenant_id)
        return resp_body['network']

    def _create_subnet(subnet_name, network_id):
        base_cidr = netaddr.IPNetwork(CONF.network.tenant_network_cidr)
        mask_bits = CONF.network.tenant_network_mask_bits
        for subnet_cidr in base_cidr.subnet(mask_bits):
            try:
                resp_body = network_admin_client.\
                    create_subnet(
                        network_id=network_id, cidr=str(subnet_cidr),
                        name=subnet_name,
                        tenant_id=tenant_id,
                        enable_dhcp=True,
                        ip_version=4)
                break
            except tempest_lib.exceptions.BadRequest as e:
                if 'overlaps with another subnet' not in str(e):
                    raise
        else:
            message = 'Available CIDR for subnet creation could not be found'
            raise Exception(message)
        return resp_body['subnet']

    def _create_router(router_name):
        external_net_id = dict(
            network_id=CONF.network.public_network_id)
        resp_body = network_admin_client.create_router(
            router_name,
            external_gateway_info=external_net_id,
            tenant_id=tenant_id)
        return resp_body['router']

    def _add_router_interface(router_id, subnet_id):
        network_admin_client.add_router_interface_with_subnet_id(
            router_id, subnet_id)

    network_name = name + "-network"
    network = _create_network(network_name)
    subnet_name = name + "-subnet"
    subnet = _create_subnet(subnet_name, network['id'])
    router_name = name + "-router"
    router = _create_router(router_name)
    _add_router_interface(router['id'], subnet['id'])
    return network_name, router_name


def random_user_name(tag, prefix):
    if tag:
        return data_utils.rand_name('-'.join((tag, prefix)))
    else:
        return data_utils.rand_name(prefix)


def generate_resources(opts):
    spec = [{'number': 1,
             'prefix': 'primary',
             'roles': (CONF.auth.tempest_roles +
                       [CONF.object_storage.operator_role])},
            {'number': 1,
             'prefix': 'alt',
             'roles': (CONF.auth.tempest_roles +
                       [CONF.object_storage.operator_role])},
            {'number': 1,
             'prefix': 'swift_admin',
             'roles': (CONF.auth.tempest_roles +
                       [CONF.object_storage.operator_role,
                        CONF.object_storage.reseller_admin_role])},
            {'number': 1,
             'prefix': 'stack_owner',
             'roles': (CONF.auth.tempest_roles +
                       [CONF.orchestration.stack_owner_role])},
            ]
    if opts.admin:
        spec.append({
            'number': 1,
            'prefix': 'admin',
            'roles': (CONF.auth.tempest_roles +
                      [CONF.identity.admin_role])
        })
    resources = {'tenants': [],
                 'users': []}
    for count in range(opts.concurrency):
        for user_group in spec:
            users = [random_user_name(opts.tag, user_group['prefix'])
                     for _ in range(user_group['number'])]
            for user in users:
                tenant = '-'.join((user, 'tenant'))
                resources['tenants'].append(tenant)
                resources['users'].append({
                    'tenant': tenant,
                    'name': user,
                    'pass': data_utils.rand_name(),
                    'prefix': user_group['prefix'],
                    'roles': user_group['roles']
                })
    return resources


def dump_accounts(opts, resources):
    accounts = []
    for user in resources['users']:
        account = {
            'username': user['name'],
            'tenant_name': user['tenant'],
            'password': user['pass'],
            'roles': user['roles']
        }
        if 'network' or 'router' in user:
            account['resources'] = {}
        if 'network' in user:
            account['resources']['network'] = user['network']
        if 'router' in user:
            account['resources']['router'] = user['router']
        accounts.append(account)
    if os.path.exists(opts.accounts):
        os.rename(opts.accounts, '.'.join((opts.accounts, 'bak')))
    with open(opts.accounts, 'w') as f:
        yaml.dump(accounts, f, default_flow_style=False)
    LOG.info('%s generated successfully!' % opts.accounts)


def get_options():
    usage_string = ('tempest-account-generator [-h] <ARG> ...\n\n'
                    'To see help on specific argument, do:\n'
                    'tempest-account-generator <ARG> -h')
    parser = argparse.ArgumentParser(
        description='Create accounts.yaml file for concurrent test runs. '
                    'One primary user, one alt user, '
                    'one swift admin, one stack owner '
                    'and one admin (optionally) will be created '
                    'for each concurrent thread.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=usage_string
    )

    parser.add_argument('-c', '--config-file',
                        metavar='/etc/tempest.conf',
                        help='path to tempest config file')
    parser.add_argument('--os-username',
                        metavar='<auth-user-name>',
                        default=os.environ.get('OS_USERNAME'),
                        help='User should have permissions '
                             'to create new user accounts and '
                             'tenants. Defaults to env[OS_USERNAME].')
    parser.add_argument('--os-password',
                        metavar='<auth-password>',
                        default=os.environ.get('OS_PASSWORD'),
                        help='Defaults to env[OS_PASSWORD].')
    parser.add_argument('--os-tenant-name',
                        metavar='<auth-tenant-name>',
                        default=os.environ.get('OS_TENANT_NAME'),
                        help='Defaults to env[OS_TENANT_NAME].')
    parser.add_argument('--tag',
                        default='',
                        required=False,
                        dest='tag',
                        help='Resources tag')
    parser.add_argument('-r', '--concurrency',
                        default=1,
                        type=int,
                        required=True,
                        dest='concurrency',
                        help='Concurrency count')
    parser.add_argument('--with-admin',
                        action='store_true',
                        dest='admin',
                        help='Creates admin for each concurrent group')
    parser.add_argument('accounts',
                        metavar='accounts_file.yaml',
                        help='Output accounts yaml file')

    opts = parser.parse_args()
    if opts.config_file:
        config.CONF.set_config_path(opts.config_file)
    return opts


def main(opts=None):
    if not opts:
        opts = get_options()
    setup_logging()
    resources = generate_resources(opts)
    create_resources(opts, resources)
    dump_accounts(opts, resources)

if __name__ == "__main__":
    main()
