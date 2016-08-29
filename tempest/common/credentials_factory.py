# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from oslo_concurrency import lockutils

from tempest import clients
from tempest.common import dynamic_creds
from tempest.common import preprov_creds
from tempest import config
from tempest import exceptions
from tempest.lib import auth

CONF = config.CONF


"""This module provides factories of credential and credential providers

Credentials providers and clients are (going to be) part of tempest.lib,
and so they may not hold any dependency to tempest configuration.

Methods in this module collect the relevant configuration details and pass
them to credentials providers and clients, so that test can have easy
access to these features.

Client managers with hard-coded configured credentials are also moved here,
to avoid circular dependencies."""

# === Credential Providers


# Subset of the parameters of credential providers that depend on configuration
def get_common_provider_params():
    return {
        'credentials_domain': CONF.auth.default_credentials_domain_name,
        'admin_role': CONF.identity.admin_role
    }


def get_dynamic_provider_params():
    return get_common_provider_params()


def get_preprov_provider_params():
    _common_params = get_common_provider_params()
    reseller_admin_role = CONF.object_storage.reseller_admin_role
    return dict(_common_params, **dict([
        ('accounts_lock_dir', lockutils.get_lock_path(CONF)),
        ('test_accounts_file', CONF.auth.test_accounts_file),
        ('object_storage_operator_role', CONF.object_storage.operator_role),
        ('object_storage_reseller_admin_role', reseller_admin_role)
    ]))


# Return the right implementation of CredentialProvider based on config
# Dropping interface and password, as they are never used anyways
# TODO(andreaf) Drop them from the CredentialsProvider interface completely
def get_credentials_provider(name, network_resources=None,
                             force_tenant_isolation=False,
                             identity_version=None):
    # If a test requires a new account to work, it can have it via forcing
    # dynamic credentials. A new account will be produced only for that test.
    # In case admin credentials are not available for the account creation,
    # the test should be skipped else it would fail.
    identity_version = identity_version or CONF.identity.auth_version
    if CONF.auth.use_dynamic_credentials or force_tenant_isolation:
        admin_creds = get_configured_admin_credentials(
            fill_in=True, identity_version=identity_version)
        return dynamic_creds.DynamicCredentialProvider(
            name=name,
            network_resources=network_resources,
            identity_version=identity_version,
            admin_creds=admin_creds,
            **get_dynamic_provider_params())
    else:
        if CONF.auth.test_accounts_file:
            # Most params are not relevant for pre-created accounts
            return preprov_creds.PreProvisionedCredentialProvider(
                name=name, identity_version=identity_version,
                **get_preprov_provider_params())
        else:
            raise exceptions.InvalidConfiguration(
                'A valid credential provider is needed')


# We want a helper function here to check and see if admin credentials
# are available so we can do a single call from skip_checks if admin
# creds area available.
# This depends on identity_version as there may be admin credentials
# available for v2 but not for v3.
def is_admin_available(identity_version):
    is_admin = True
    # If dynamic credentials is enabled admin will be available
    if CONF.auth.use_dynamic_credentials:
        return is_admin
    # Check whether test accounts file has the admin specified or not
    elif CONF.auth.test_accounts_file:
        check_accounts = preprov_creds.PreProvisionedCredentialProvider(
            identity_version=identity_version, name='check_admin',
            **get_preprov_provider_params())
        if not check_accounts.admin_available():
            is_admin = False
    else:
        try:
            get_configured_admin_credentials(fill_in=False,
                                             identity_version=identity_version)
        except exceptions.InvalidConfiguration:
            is_admin = False
    return is_admin


# We want a helper function here to check and see if alt credentials
# are available so we can do a single call from skip_checks if alt
# creds area available.
# This depends on identity_version as there may be alt credentials
# available for v2 but not for v3.
def is_alt_available(identity_version):
    # If dynamic credentials is enabled alt will be available
    if CONF.auth.use_dynamic_credentials:
        return True
    # Check whether test accounts file has the admin specified or not
    if CONF.auth.test_accounts_file:
        check_accounts = preprov_creds.PreProvisionedCredentialProvider(
            identity_version=identity_version, name='check_alt',
            **get_preprov_provider_params())
    else:
        raise exceptions.InvalidConfiguration(
            'A valid credential provider is needed')

    try:
        if not check_accounts.is_multi_user():
            return False
        else:
            return True
    except exceptions.InvalidConfiguration:
        return False

# === Credentials

# Type of credentials available from configuration
CREDENTIAL_TYPES = {
    'identity_admin': ('auth', 'admin'),
    'user': ('identity', None),
    'alt_user': ('identity', 'alt')
}

DEFAULT_PARAMS = {
    'disable_ssl_certificate_validation':
        CONF.identity.disable_ssl_certificate_validation,
    'ca_certs': CONF.identity.ca_certificates_file,
    'trace_requests': CONF.debug.trace_requests
}


# Read credentials from configuration, builds a Credentials object
# based on the specified or configured version
def get_configured_admin_credentials(fill_in=True, identity_version=None):
    identity_version = identity_version or CONF.identity.auth_version

    if identity_version not in ('v2', 'v3'):
        raise exceptions.InvalidConfiguration(
            'Unsupported auth version: %s' % identity_version)

    conf_attributes = ['username', 'password',
                       'project_name']

    if identity_version == 'v3':
        conf_attributes.append('domain_name')
    # Read the parts of credentials from config
    params = DEFAULT_PARAMS.copy()
    for attr in conf_attributes:
        params[attr] = getattr(CONF.auth, 'admin_' + attr)
    # Build and validate credentials. We are reading configured credentials,
    # so validate them even if fill_in is False
    credentials = get_credentials(fill_in=fill_in,
                                  identity_version=identity_version, **params)
    if not fill_in:
        if not credentials.is_valid():
            msg = ("The admin credentials are incorrectly set in the config "
                   "file for identity version %s. Double check that all "
                   "required values are assigned.")
            raise exceptions.InvalidConfiguration(msg % identity_version)
    return credentials


# Wrapper around auth.get_credentials to use the configured identity version
# if none is specified
def get_credentials(fill_in=True, identity_version=None, **kwargs):
    params = dict(DEFAULT_PARAMS, **kwargs)
    identity_version = identity_version or CONF.identity.auth_version
    # In case of "v3" add the domain from config if not specified
    # To honour the "default_credentials_domain_name", if not domain
    # field is specified at all, add it the credential dict.
    if identity_version == 'v3':
        domain_fields = set(x for x in auth.KeystoneV3Credentials.ATTRIBUTES
                            if 'domain' in x)
        if not domain_fields.intersection(kwargs.keys()):
            domain_name = CONF.auth.default_credentials_domain_name
            # NOTE(andreaf) Setting domain_name implicitly sets user and
            # project domain names, if they are None
            params['domain_name'] = domain_name

        auth_url = CONF.identity.uri_v3
    else:
        auth_url = CONF.identity.uri
    return auth.get_credentials(auth_url,
                                fill_in=fill_in,
                                identity_version=identity_version,
                                **params)

# === Credential / client managers


class AdminManager(clients.Manager):
    """Manager that uses admin credentials for its managed client objects"""

    def __init__(self, service=None):
        super(AdminManager, self).__init__(
            credentials=get_configured_admin_credentials(),
            service=service)
