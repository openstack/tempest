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
from tempest import config
from tempest.lib import auth
from tempest.lib.common import dynamic_creds
from tempest.lib.common import preprov_creds
from tempest.lib import exceptions

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
def _get_common_provider_params(identity_version):
    if identity_version == 'v3':
        identity_uri = CONF.identity.uri_v3
    elif identity_version == 'v2':
        identity_uri = CONF.identity.uri
    else:
        raise exceptions.InvalidIdentityVersion(
            identity_version=identity_version)
    return {
        'identity_version': identity_version,
        'identity_uri': identity_uri,
        'credentials_domain': CONF.auth.default_credentials_domain_name,
        'admin_role': CONF.identity.admin_role
    }


def get_dynamic_provider_params(identity_version, admin_creds=None):
    """Dynamic provider parameters setup from config

    This helper returns a dict of parameter that can be used to initialise
    a `DynamicCredentialProvider` according to tempest configuration.
    Parameters that are not configuration specific (name, network_resources)
    are not returned.

    :param identity_version: 'v2' or 'v3'
    :param admin_creds: An object of type `auth.Credentials`. If None, it
                        is built from the configuration file as well.
    :return: A dict with the parameters
    """
    _common_params = _get_common_provider_params(identity_version)
    admin_creds = admin_creds or get_configured_admin_credentials(
        fill_in=True, identity_version=identity_version)
    if identity_version == 'v3':
        endpoint_type = CONF.identity.v3_endpoint_type
    elif identity_version == 'v2':
        endpoint_type = CONF.identity.v2_admin_endpoint_type
    return dict(_common_params, **dict([
        ('admin_creds', admin_creds),
        ('identity_admin_domain_scope', CONF.identity.admin_domain_scope),
        ('identity_admin_role', CONF.identity.admin_role),
        ('extra_roles', CONF.auth.tempest_roles),
        ('neutron_available', CONF.service_available.neutron),
        ('project_network_cidr', CONF.network.project_network_cidr),
        ('project_network_mask_bits', CONF.network.project_network_mask_bits),
        ('public_network_id', CONF.network.public_network_id),
        ('create_networks', (CONF.auth.create_isolated_networks and not
                             CONF.network.shared_physical_network)),
        ('resource_prefix', 'tempest'),
        ('identity_admin_endpoint_type', endpoint_type)
    ]))


def get_preprov_provider_params(identity_version):
    """Pre-provisioned provider parameters setup from config

    This helper returns a dict of parameter that can be used to initialise
    a `PreProvisionedCredentialProvider` according to tempest configuration.
    Parameters that are not configuration specific (name) are not returned.

    :param identity_version: 'v2' or 'v3'
    :return: A dict with the parameters
    """
    _common_params = _get_common_provider_params(identity_version)
    reseller_admin_role = CONF.object_storage.reseller_admin_role
    return dict(_common_params, **dict([
        ('accounts_lock_dir', lockutils.get_lock_path(CONF)),
        ('test_accounts_file', CONF.auth.test_accounts_file),
        ('object_storage_operator_role', CONF.object_storage.operator_role),
        ('object_storage_reseller_admin_role', reseller_admin_role)
    ]))


def get_credentials_provider(name, network_resources=None,
                             force_tenant_isolation=False,
                             identity_version=None):
    """Return the right implementation of CredentialProvider based on config

    This helper returns the right implementation of CredentialProvider based on
    config and on the value of force_tenant_isolation.

    :param name: When provided, it makes it possible to associate credential
                 artifacts back to the owner (test class).
    :param network_resources: Dictionary of network resources to be allocated
                              for each test account. Only valid for the dynamic
                              credentials provider.
    :param force_tenant_isolation: Always return a `DynamicCredentialProvider`,
                                   regardless of the configuration.
    :param identity_version: Use the specified identity API version, regardless
                             of the configuration. Valid values are 'v2', 'v3'.
    """
    # If a test requires a new account to work, it can have it via forcing
    # dynamic credentials. A new account will be produced only for that test.
    # In case admin credentials are not available for the account creation,
    # the test should be skipped else it would fail.
    identity_version = identity_version or CONF.identity.auth_version
    if CONF.auth.use_dynamic_credentials or force_tenant_isolation:
        return dynamic_creds.DynamicCredentialProvider(
            name=name,
            network_resources=network_resources,
            **get_dynamic_provider_params(identity_version))
    else:
        if CONF.auth.test_accounts_file:
            # Most params are not relevant for pre-created accounts
            return preprov_creds.PreProvisionedCredentialProvider(
                name=name,
                **get_preprov_provider_params(identity_version))
        else:
            raise exceptions.InvalidConfiguration(
                'A valid credential provider is needed')


def is_admin_available(identity_version):
    """Helper to check for admin credentials

    Helper function to check if a set of admin credentials is available so we
    can do a single call from skip_checks.
    This helper depends on identity_version as there may be admin credentials
    available for v2 but not for v3.

    :param identity_version: 'v2' or 'v3'
    """
    is_admin = True
    # If dynamic credentials is enabled admin will be available
    if CONF.auth.use_dynamic_credentials:
        return is_admin
    # Check whether test accounts file has the admin specified or not
    elif CONF.auth.test_accounts_file:
        check_accounts = preprov_creds.PreProvisionedCredentialProvider(
            name='check_admin',
            **get_preprov_provider_params(identity_version))
        if not check_accounts.admin_available():
            is_admin = False
    else:
        try:
            get_configured_admin_credentials(fill_in=False,
                                             identity_version=identity_version)
        except exceptions.InvalidConfiguration:
            is_admin = False
    return is_admin


def is_alt_available(identity_version):
    """Helper to check for alt credentials

    Helper function to check if a second set of credentials is available (aka
    alt credentials) so we can do a single call from skip_checks.
    This helper depends on identity_version as there may be alt credentials
    available for v2 but not for v3.

    :param identity_version: 'v2' or 'v3'
    """
    # If dynamic credentials is enabled alt will be available
    if CONF.auth.use_dynamic_credentials:
        return True
    # Check whether test accounts file has the admin specified or not
    if CONF.auth.test_accounts_file:
        check_accounts = preprov_creds.PreProvisionedCredentialProvider(
            name='check_alt',
            **get_preprov_provider_params(identity_version))
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


def get_configured_admin_credentials(fill_in=True, identity_version=None):
    """Get admin credentials from the config file

    Read credentials from configuration, builds a Credentials object based on
    the specified or configured version

    :param fill_in: If True, a request to the Token API is submitted, and the
                    credential object is filled in with all names and IDs from
                    the token API response.
    :param identity_version: The identity version to talk to and the type of
                             credentials object to be created. 'v2' or 'v3'.
    :returns: An object of a sub-type of `auth.Credentials`
    """
    identity_version = identity_version or CONF.identity.auth_version

    if identity_version not in ('v2', 'v3'):
        raise exceptions.InvalidConfiguration(
            'Unsupported auth version: %s' % identity_version)

    conf_attributes = ['username', 'password',
                       'project_name']

    if identity_version == 'v3':
        conf_attributes.append('domain_name')
    # Read the parts of credentials from config
    params = config.service_client_config()
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


def get_credentials(fill_in=True, identity_version=None, **kwargs):
    """Get credentials from dict based on config

    Wrapper around auth.get_credentials to use the configured identity version
    if none is specified.

    :param fill_in: If True, a request to the Token API is submitted, and the
                    credential object is filled in with all names and IDs from
                    the token API response.
    :param identity_version: The identity version to talk to and the type of
                             credentials object to be created. 'v2' or 'v3'.
    :param kwargs: Attributes to be used to build the Credentials object.
    :returns: An object of a sub-type of `auth.Credentials`
    """
    params = dict(config.service_client_config(), **kwargs)
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

    def __init__(self):
        super(AdminManager, self).__init__(
            credentials=get_configured_admin_credentials())
