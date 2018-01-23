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
Utility for creating ``accounts.yaml`` file for concurrent test runs.
Creates one primary user, one alt user, one swift admin, one stack owner
and one admin (optionally) for each concurrent thread. The utility creates
user for each tenant. The ``accounts.yaml`` file will be valid and contain
credentials for created users, so each user will be in separate tenant and
have the username, tenant_name, password and roles.

**Usage:** ``tempest account-generator [-h] [OPTIONS] accounts_file.yaml``

Positional Arguments
--------------------
``accounts_file.yaml`` (Required) Provide an output accounts yaml file. Utility
creates a .yaml file in the directory where the command is ran. The appropriate
name for the file is *accounts.yaml* and it should be placed in *tempest/etc*
directory.

Authentication
--------------

Account generator creates users and tenants so it needs the admin credentials
of your cloud to operate properly. The corresponding info can be given either
through CLI options or environment variables.

You're probably familiar with these, but just to remind:

======== ============================ ====================
Param    CLI                          Environment Variable
======== ============================ ====================
Username ``--os-username``            OS_USERNAME
Password ``--os-password``            OS_PASSWORD
Project  ``--os-project-name``        OS_PROJECT_NAME
Tenant   ``--os-tenant-name`` (depr.) OS_TENANT_NAME
Domain   ``--os-domain-name``         OS_DOMAIN_NAME
======== ============================ ====================

Optional Arguments
------------------
* ``-h, --help`` (Optional) Shows help message with the description of
  utility and its arguments, and exits.

* ``-c, --config-file /etc/tempest.conf`` (Optional) Path
  to tempest config file. If not specified, it searches for tempest.conf in
  these locations:

  - ./etc/
  - /etc/tempest
  - ~/.tempest/
  - ~/
  - /etc/

* ``--os-username <auth-user-name>`` (Optional) Name used for authentication
  with the OpenStack Identity service. Defaults to env[OS_USERNAME]. Note: User
  should have permissions to create new user accounts and tenants.

* ``--os-password <auth-password>`` (Optional) Password used for authentication
  with the OpenStack Identity service. Defaults to env[OS_PASSWORD].

* ``--os-project-name <auth-project-name>`` (Optional) Project to request
  authorization on. Defaults to env[OS_PROJECT_NAME].

* ``--os-tenant-name <auth-tenant-name>`` (Optional, deprecated) Tenant to
  request authorization on. Defaults to env[OS_TENANT_NAME].

* ``--os-domain-name <auth-domain-name>`` (Optional) Domain the user and
  project belong to. Defaults to env[OS_DOMAIN_NAME].

* ``--tag TAG`` (Optional) Resources tag. Each created resource (user, project)
  will have the prefix with the given TAG in its name. Using tag is recommended
  for the further using, cleaning resources.

* ``-r, --concurrency CONCURRENCY`` (Optional) Concurrency count
  (default: 1). The number of accounts required can be estimated as
  CONCURRENCY x 2. Each user provided in *accounts.yaml* file will be in
  a different tenant. This is required to provide isolation between test for
  running in parallel.

* ``--with-admin`` (Optional) Creates admin for each concurrent group
  (default: False).

* ``-i, --identity-version VERSION`` (Optional) Provisions accounts
  using the specified version of the identity API. (default: '3').

To see help on specific argument, please do: ``tempest account-generator
[OPTIONS] <accounts_file.yaml> -h``.
"""
import argparse
import os
import traceback

from cliff import command
from oslo_log import log as logging
import yaml

from tempest.common import credentials_factory
from tempest import config
from tempest.lib.common import dynamic_creds


LOG = None
CONF = config.CONF
DESCRIPTION = ('Create accounts.yaml file for concurrent test runs.%s'
               'One primary user, one alt user, '
               'one swift admin, one stack owner '
               'and one admin (optionally) will be created '
               'for each concurrent thread.' % os.linesep)


def setup_logging():
    global LOG
    logging.setup(CONF, __name__)
    LOG = logging.getLogger(__name__)


def get_credential_provider(opts):
    identity_version = "".join(['v', str(opts.identity_version)])
    # NOTE(andreaf) For now tempest.conf controls whether resources will
    # actually be created. Once we remove the dependency from tempest.conf
    # we will need extra CLI option(s) to control this.
    network_resources = {'router': True,
                         'network': True,
                         'subnet': True,
                         'dhcp': True}
    admin_creds_dict = {'username': opts.os_username,
                        'password': opts.os_password}
    _project_name = opts.os_project_name or opts.os_tenant_name
    if opts.identity_version == 3:
        admin_creds_dict['project_name'] = _project_name
        admin_creds_dict['domain_name'] = opts.os_domain_name or 'Default'
    elif opts.identity_version == 2:
        admin_creds_dict['tenant_name'] = _project_name
    admin_creds = credentials_factory.get_credentials(
        fill_in=False, identity_version=identity_version, **admin_creds_dict)
    return dynamic_creds.DynamicCredentialProvider(
        name=opts.tag,
        network_resources=network_resources,
        **credentials_factory.get_dynamic_provider_params(
            identity_version, admin_creds=admin_creds))


def generate_resources(cred_provider, admin):
    # Create the list of resources to be provisioned for each process
    # NOTE(andreaf) get_credentials expects a string for types or a list for
    # roles. Adding all required inputs to the spec list.
    spec = ['primary', 'alt']
    if CONF.service_available.swift:
        spec.append([CONF.object_storage.operator_role])
        spec.append([CONF.object_storage.reseller_admin_role])
        spec.append([CONF.object_storage.operator_role])
    if admin:
        spec.append('admin')
    resources = []
    for cred_type in spec:
        resources.append((cred_type, cred_provider.get_credentials(
            credential_type=cred_type)))
    return resources


def dump_accounts(resources, identity_version, account_file):
    accounts = []
    for resource in resources:
        cred_type, test_resource = resource
        account = {
            'username': test_resource.username,
            'password': test_resource.password
        }
        if identity_version == 3:
            account['project_name'] = test_resource.project_name
            account['domain_name'] = test_resource.domain_name
        else:
            account['project_name'] = test_resource.tenant_name

        # If the spec includes 'admin' credentials are defined via type,
        # else they are defined via list of roles.
        if cred_type == 'admin':
            account['types'] = [cred_type]
        elif cred_type not in ['primary', 'alt']:
            account['roles'] = cred_type

        if test_resource.network:
            account['resources'] = {}
        if test_resource.network:
            account['resources']['network'] = test_resource.network['name']
        accounts.append(account)
    if os.path.exists(account_file):
        os.rename(account_file, '.'.join((account_file, 'bak')))
    with open(account_file, 'w') as f:
        yaml.safe_dump(accounts, f, default_flow_style=False)
    LOG.info('%s generated successfully!', account_file)


def _parser_add_args(parser):
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
    parser.add_argument('--os-project-name',
                        metavar='<auth-project-name>',
                        default=os.environ.get('OS_PROJECT_NAME'),
                        help='Defaults to env[OS_PROJECT_NAME].')
    parser.add_argument('--os-tenant-name',
                        metavar='<auth-tenant-name>',
                        default=os.environ.get('OS_TENANT_NAME'),
                        help='Defaults to env[OS_TENANT_NAME].')
    parser.add_argument('--os-domain-name',
                        metavar='<auth-domain-name>',
                        default=os.environ.get('OS_DOMAIN_NAME'),
                        help='Defaults to env[OS_DOMAIN_NAME].')
    parser.add_argument('--tag',
                        default='',
                        required=False,
                        dest='tag',
                        help='Resources tag')
    parser.add_argument('-r', '--concurrency',
                        default=1,
                        type=int,
                        required=False,
                        dest='concurrency',
                        help='Concurrency count')
    parser.add_argument('--with-admin',
                        action='store_true',
                        dest='admin',
                        help='Creates admin for each concurrent group')
    parser.add_argument('-i', '--identity-version',
                        default=3,
                        choices=[2, 3],
                        type=int,
                        required=False,
                        dest='identity_version',
                        help='Version of the Identity API to use')
    parser.add_argument('accounts',
                        metavar='accounts_file.yaml',
                        help='Output accounts yaml file')


def get_options():
    usage_string = ('tempest account-generator [-h] <ARG> ...\n\n'
                    'To see help on specific argument, do:\n'
                    'tempest account-generator <ARG> -h')
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=usage_string
    )

    _parser_add_args(parser)
    opts = parser.parse_args()
    return opts


class TempestAccountGenerator(command.Command):

    def get_parser(self, prog_name):
        parser = super(TempestAccountGenerator, self).get_parser(prog_name)
        _parser_add_args(parser)
        return parser

    def take_action(self, parsed_args):
        try:
            main(parsed_args)
        except Exception:
            LOG.exception("Failure generating test accounts.")
            traceback.print_exc()
            raise

    def get_description(self):
        return DESCRIPTION


def main(opts=None):
    setup_logging()
    if not opts:
        LOG.warning("Use of: 'tempest-account-generator' is deprecated, "
                    "please use: 'tempest account-generator'")
        opts = get_options()
    if opts.config_file:
        config.CONF.set_config_path(opts.config_file)
    if opts.os_tenant_name:
        LOG.warning("'os-tenant-name' and 'OS_TENANT_NAME' are both "
                    "deprecated, please use 'os-project-name' or "
                    "'OS_PROJECT_NAME' instead")
    resources = []
    for count in range(opts.concurrency):
        # Use N different cred_providers to obtain different sets of creds
        cred_provider = get_credential_provider(opts)
        resources.extend(generate_resources(cred_provider, opts.admin))
    dump_accounts(resources, opts.identity_version, opts.accounts)

if __name__ == "__main__":
    main()
