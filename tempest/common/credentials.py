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

from tempest.common import accounts
from tempest.common import isolated_creds
from tempest import config

CONF = config.CONF


# Return the right implementation of CredentialProvider based on config
# Dropping interface and password, as they are never used anyways
# TODO(andreaf) Drop them from the CredentialsProvider interface completely
def get_isolated_credentials(name, network_resources=None,
                             force_tenant_isolation=False):
    # If a test requires a new account to work, it can have it via forcing
    # tenant isolation. A new account will be produced only for that test.
    # In case admin credentials are not available for the account creation,
    # the test should be skipped else it would fail.
    if CONF.auth.allow_tenant_isolation or force_tenant_isolation:
        return isolated_creds.IsolatedCreds(
            name=name,
            network_resources=network_resources)
    else:
        if CONF.auth.locking_credentials_provider:
            # Most params are not relevant for pre-created accounts
            return accounts.Accounts(name=name)
        else:
            return accounts.NotLockingAccounts(name=name)
