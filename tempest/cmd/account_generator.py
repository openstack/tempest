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

import argparse
import os

from oslo_log import log as logging
import yaml

from tempest import config
from tempest import exceptions
from tempest.services.identity.v2.json import identity_client
import tempest_lib.auth
from tempest_lib.common.utils import data_utils
import tempest_lib.exceptions

LOG = None
CONF = config.CONF


def setup_logging():
    global LOG
    logging.setup(CONF, __name__)
    LOG = logging.getLogger(__name__)


def keystone_admin(opts):
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
    return identity_client.IdentityClientJSON(
        _auth,
        CONF.identity.catalog_type,
        CONF.identity.region,
        endpoint_type='adminURL',
        **params
    )


def create_resources(opts, resources):
    admin = keystone_admin(opts)
    roles = admin.list_roles()
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
    existing = [x['name'] for x in admin.list_tenants()]
    for tenant in resources['tenants']:
        if tenant not in existing:
            admin.create_tenant(tenant)
        else:
            LOG.warn("Tenant '%s' already exists in this environment" % tenant)
    LOG.info('Tenants created')
    for u in resources['users']:
        try:
            tenant = admin.get_tenant_by_name(u['tenant'])
        except tempest_lib.exceptions.NotFound:
            LOG.error("Tenant: %s - not found" % u['tenant'])
            continue
        while True:
            try:
                admin.get_user_by_username(tenant['id'], u['name'])
            except tempest_lib.exceptions.NotFound:
                admin.create_user(
                    u['name'], u['pass'], tenant['id'],
                    "%s@%s" % (u['name'], tenant['id']),
                    enabled=True)
                break
            else:
                LOG.warn("User '%s' already exists in this environment. "
                         "New name generated" % u['name'])
                u['name'] = random_user_name(opts.tag, u['prefix'])

    LOG.info('Users created')
    for u in resources['users']:
        try:
            tenant = admin.get_tenant_by_name(u['tenant'])
        except tempest_lib.exceptions.NotFound:
            LOG.error("Tenant: %s - not found" % u['tenant'])
            continue
        try:
            user = admin.get_user_by_username(tenant['id'],
                                              u['name'])
        except tempest_lib.exceptions.NotFound:
            LOG.error("User: %s - not found" % u['user'])
            continue
        for r in u['role_ids']:
            try:
                admin.assign_user_role(tenant['id'], user['id'], r)
            except tempest_lib.exceptions.Conflict:
                # don't care if it's already assigned
                pass
    LOG.info('Roles assigned')
    LOG.info('Resources deployed successfully!')


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
        accounts.append({
            'username': user['name'],
            'tenant_name': user['tenant'],
            'password': user['pass'],
            'roles': user['roles']
        })
    if os.path.exists(opts.accounts):
        os.rename(opts.accounts, '.'.join((opts.accounts, 'bak')))
    with open(opts.accounts, 'w') as f:
        yaml.dump(accounts, f, default_flow_style=False)
    LOG.info('%s generated successfully!' % opts.accounts)


def get_options():
    usage_string = ('account_generator [-h] <ARG> ...\n\n'
                    'To see help on specific argument, do:\n'
                    'account_generator <ARG> -h')
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
                        help='User should have permitions '
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
                        help='Create admin in every tenant')
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
