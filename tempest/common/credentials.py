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

import os

from tempest.common import cred_provider
from tempest.common import dynamic_creds
from tempest.common import preprov_creds
from tempest import config
from tempest import exceptions

CONF = config.CONF


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
        return dynamic_creds.DynamicCredentialProvider(
            name=name,
            network_resources=network_resources,
            identity_version=identity_version)
    else:
        if (CONF.auth.test_accounts_file and
                os.path.isfile(CONF.auth.test_accounts_file)):
            # Most params are not relevant for pre-created accounts
            return preprov_creds.PreProvisionedCredentialProvider(
                name=name, identity_version=identity_version)
        else:
            return preprov_creds.NonLockingCredentialProvider(
                name=name, identity_version=identity_version)


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
    elif (CONF.auth.test_accounts_file and
            os.path.isfile(CONF.auth.test_accounts_file)):
        check_accounts = preprov_creds.PreProvisionedCredentialProvider(
            identity_version=identity_version, name='check_admin')
        if not check_accounts.admin_available():
            is_admin = False
    else:
        try:
            cred_provider.get_configured_credentials(
                'identity_admin', fill_in=False,
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
    if (CONF.auth.test_accounts_file and
            os.path.isfile(CONF.auth.test_accounts_file)):
        check_accounts = preprov_creds.PreProvisionedCredentialProvider(
            identity_version=identity_version, name='check_alt')
    else:
        check_accounts = preprov_creds.NonLockingCredentialProvider(
            identity_version=identity_version, name='check_alt')
    try:
        if not check_accounts.is_multi_user():
            return False
        else:
            return True
    except exceptions.InvalidConfiguration:
        return False
