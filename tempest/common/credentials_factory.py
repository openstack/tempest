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
from tempest.common import cred_provider
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
def _get_common_provider_params():
    return {
        'credentials_domain': CONF.auth.default_credentials_domain_name,
        'admin_role': CONF.identity.admin_role
    }


def _get_dynamic_provider_params():
    return _get_common_provider_params()


def _get_preprov_provider_params():
    _common_params = _get_common_provider_params()
    reseller_admin_role = CONF.object_storage.reseller_admin_role
    return dict(_common_params, **dict([
        ('accounts_lock_dir', lockutils.get_lock_path(CONF)),
        ('test_accounts_file', CONF.auth.test_accounts_file),
        ('object_storage_operator_role', CONF.object_storage.operator_role),
        ('object_storage_reseller_admin_role', reseller_admin_role)
    ]))


class LegacyCredentialProvider(cred_provider.CredentialProvider):

    def __init__(self, identity_version):
        """Credentials provider which returns credentials from tempest.conf

        Credentials provider which always returns the first and second
        configured accounts as primary and alt users.
        Credentials from tempest.conf are deprecated, and this credential
        provider is also accordingly.

        This credential provider can be used in case of serial test execution
        to preserve the current behaviour of the serial tempest run.

        :param identity_version: Version of the identity API
        :return: CredentialProvider
        """
        super(LegacyCredentialProvider, self).__init__(
            identity_version=identity_version)
        self._creds = {}

    def _unique_creds(self, cred_arg=None):
        """Verify that the configured credentials are valid and distinct """
        try:
            user = self.get_primary_creds()
            alt_user = self.get_alt_creds()
            return getattr(user, cred_arg) != getattr(alt_user, cred_arg)
        except exceptions.InvalidCredentials as ic:
            msg = "At least one of the configured credentials is " \
                  "not valid: %s" % ic.message
            raise exceptions.InvalidConfiguration(msg)

    def is_multi_user(self):
        return self._unique_creds('username')

    def is_multi_tenant(self):
        return self._unique_creds('tenant_id')

    def get_primary_creds(self):
        if self._creds.get('primary'):
            return self._creds.get('primary')
        primary_credential = get_configured_credentials(
            credential_type='user', fill_in=False,
            identity_version=self.identity_version)
        self._creds['primary'] = cred_provider.TestResources(
            primary_credential)
        return self._creds['primary']

    def get_alt_creds(self):
        if self._creds.get('alt'):
            return self._creds.get('alt')
        alt_credential = get_configured_credentials(
            credential_type='alt_user', fill_in=False,
            identity_version=self.identity_version)
        self._creds['alt'] = cred_provider.TestResources(
            alt_credential)
        return self._creds['alt']

    def clear_creds(self):
        self._creds = {}

    def get_admin_creds(self):
        if self._creds.get('admin'):
            return self._creds.get('admin')
        creds = get_configured_credentials(
            "identity_admin", fill_in=False)
        self._creds['admin'] = cred_provider.TestResources(creds)
        return self._creds['admin']

    def get_creds_by_roles(self, roles, force_new=False):
        msg = "Credentials being specified through the config file can not be"\
              " used with tests that specify using credentials by roles. "\
              "Either exclude/skip the tests doing this or use either a "\
              "test_accounts_file or dynamic credentials."
        raise exceptions.InvalidConfiguration(msg)

    def is_role_available(self, role):
        # NOTE(andreaf) LegacyCredentialProvider does not support credentials
        # by role, so returning always False.
        # Test that rely on credentials by role should use this to skip
        # when this is credential provider is used
        return False


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
        admin_creds = get_configured_credentials(
            'identity_admin', fill_in=True, identity_version=identity_version)
        return dynamic_creds.DynamicCredentialProvider(
            name=name,
            network_resources=network_resources,
            identity_version=identity_version,
            admin_creds=admin_creds,
            **_get_dynamic_provider_params())
    else:
        if CONF.auth.test_accounts_file:
            # Most params are not relevant for pre-created accounts
            return preprov_creds.PreProvisionedCredentialProvider(
                name=name, identity_version=identity_version,
                **_get_preprov_provider_params())
        else:
            # Dynamic credentials are disabled, and the account file is not
            # defined - we fall back on credentials configured in tempest.conf
            return LegacyCredentialProvider(identity_version=identity_version)


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
            **_get_preprov_provider_params())
        if not check_accounts.admin_available():
            is_admin = False
    else:
        try:
            get_configured_credentials('identity_admin', fill_in=False,
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
            **_get_preprov_provider_params())
    else:
        check_accounts = LegacyCredentialProvider(identity_version)
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
def get_configured_credentials(credential_type, fill_in=True,
                               identity_version=None):
    identity_version = identity_version or CONF.identity.auth_version

    if identity_version not in ('v2', 'v3'):
        raise exceptions.InvalidConfiguration(
            'Unsupported auth version: %s' % identity_version)

    if credential_type not in CREDENTIAL_TYPES:
        raise exceptions.InvalidCredentials()
    conf_attributes = ['username', 'password', 'project_name']

    if identity_version == 'v3':
        conf_attributes.append('domain_name')
    # Read the parts of credentials from config
    params = DEFAULT_PARAMS.copy()
    section, prefix = CREDENTIAL_TYPES[credential_type]
    for attr in conf_attributes:
        _section = getattr(CONF, section)
        if prefix is None:
            params[attr] = getattr(_section, attr)
        else:
            params[attr] = getattr(_section, prefix + "_" + attr)
    # NOTE(andreaf) v2 API still uses tenants, so we must translate project
    # to tenant before building the Credentials object
    if identity_version == 'v2':
        params['tenant_name'] = params.get('project_name')
        params.pop('project_name', None)
    # Build and validate credentials. We are reading configured credentials,
    # so validate them even if fill_in is False
    credentials = get_credentials(fill_in=fill_in,
                                  identity_version=identity_version, **params)
    if not fill_in:
        if not credentials.is_valid():
            msg = ("The %s credentials are incorrectly set in the config file."
                   " Double check that all required values are assigned" %
                   credential_type)
            raise exceptions.InvalidConfiguration(msg)
    return credentials


# Wrapper around auth.get_credentials to use the configured identity version
# is none is specified
def get_credentials(fill_in=True, identity_version=None, **kwargs):
    params = dict(DEFAULT_PARAMS, **kwargs)
    identity_version = identity_version or CONF.identity.auth_version
    # In case of "v3" add the domain from config if not specified
    if identity_version == 'v3':
        domain_fields = set(x for x in auth.KeystoneV3Credentials.ATTRIBUTES
                            if 'domain' in x)
        if not domain_fields.intersection(kwargs.keys()):
            domain_name = CONF.auth.default_credentials_domain_name
            params['user_domain_name'] = domain_name

        auth_url = CONF.identity.uri_v3
    else:
        auth_url = CONF.identity.uri
    return auth.get_credentials(auth_url,
                                fill_in=fill_in,
                                identity_version=identity_version,
                                **params)

# === Credential / client managers


class ConfiguredUserManager(clients.Manager):
    """Manager that uses user credentials for its managed client objects"""

    def __init__(self, service=None):
        super(ConfiguredUserManager, self).__init__(
            credentials=get_configured_credentials('user'),
            service=service)


class AdminManager(clients.Manager):
    """Manager that uses admin credentials for its managed client objects"""

    def __init__(self, service=None):
        super(AdminManager, self).__init__(
            credentials=get_configured_credentials('identity_admin'),
            service=service)
