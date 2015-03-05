# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

import hashlib
import os

import yaml

from tempest.common import cred_provider
from tempest import config
from tempest import exceptions
from tempest.openstack.common import lockutils
from tempest.openstack.common import log as logging

CONF = config.CONF
LOG = logging.getLogger(__name__)


def read_accounts_yaml(path):
    yaml_file = open(path, 'r')
    accounts = yaml.load(yaml_file)
    return accounts


class Accounts(cred_provider.CredentialProvider):

    def __init__(self, name):
        super(Accounts, self).__init__(name)
        self.name = name
        if os.path.isfile(CONF.auth.test_accounts_file):
            accounts = read_accounts_yaml(CONF.auth.test_accounts_file)
            self.use_default_creds = False
        else:
            accounts = {}
            self.use_default_creds = True
        self.hash_dict = self.get_hash_dict(accounts)
        self.accounts_dir = os.path.join(CONF.lock_path, 'test_accounts')
        self.isolated_creds = {}

    @classmethod
    def get_hash_dict(cls, accounts):
        hash_dict = {}
        for account in accounts:
            temp_hash = hashlib.md5()
            temp_hash.update(str(account))
            hash_dict[temp_hash.hexdigest()] = account
        return hash_dict

    def is_multi_user(self):
        # Default credentials is not a valid option with locking Account
        if self.use_default_creds:
            raise exceptions.InvalidConfiguration(
                "Account file %s doesn't exist" % CONF.auth.test_accounts_file)
        else:
            return len(self.hash_dict) > 1

    def is_multi_tenant(self):
        return self.is_multi_user()

    def _create_hash_file(self, hash_string):
        path = os.path.join(os.path.join(self.accounts_dir, hash_string))
        if not os.path.isfile(path):
            with open(path, 'w') as fd:
                fd.write(self.name)
            return True
        return False

    @lockutils.synchronized('test_accounts_io', external=True)
    def _get_free_hash(self, hashes):
        if not os.path.isdir(self.accounts_dir):
            os.mkdir(self.accounts_dir)
            # Create File from first hash (since none are in use)
            self._create_hash_file(hashes[0])
            return hashes[0]
        names = []
        for _hash in hashes:
            res = self._create_hash_file(_hash)
            if res:
                return _hash
            else:
                path = os.path.join(os.path.join(self.accounts_dir,
                                                 _hash))
                with open(path, 'r') as fd:
                    names.append(fd.read())
        msg = ('Insufficient number of users provided. %s have allocated all '
               'the credentials for this allocation request' % ','.join(names))
        raise exceptions.InvalidConfiguration(msg)

    def _get_creds(self):
        if self.use_default_creds:
            raise exceptions.InvalidConfiguration(
                "Account file %s doesn't exist" % CONF.auth.test_accounts_file)
        free_hash = self._get_free_hash(self.hash_dict.keys())
        return self.hash_dict[free_hash]

    @lockutils.synchronized('test_accounts_io', external=True)
    def remove_hash(self, hash_string):
        hash_path = os.path.join(self.accounts_dir, hash_string)
        if not os.path.isfile(hash_path):
            LOG.warning('Expected an account lock file %s to remove, but '
                        'one did not exist' % hash_path)
        else:
            os.remove(hash_path)
            if not os.listdir(self.accounts_dir):
                os.rmdir(self.accounts_dir)

    def get_hash(self, creds):
        for _hash in self.hash_dict:
            # Comparing on the attributes that were read from the YAML
            if all([getattr(creds, k) == self.hash_dict[_hash][k] for k in
                    creds.get_init_attributes()]):
                return _hash
        raise AttributeError('Invalid credentials %s' % creds)

    def remove_credentials(self, creds):
        _hash = self.get_hash(creds)
        self.remove_hash(_hash)

    def get_primary_creds(self):
        if self.isolated_creds.get('primary'):
            return self.isolated_creds.get('primary')
        creds = self._get_creds()
        primary_credential = cred_provider.get_credentials(**creds)
        self.isolated_creds['primary'] = primary_credential
        return primary_credential

    def get_alt_creds(self):
        if self.isolated_creds.get('alt'):
            return self.isolated_creds.get('alt')
        creds = self._get_creds()
        alt_credential = cred_provider.get_credentials(**creds)
        self.isolated_creds['alt'] = alt_credential
        return alt_credential

    def clear_isolated_creds(self):
        for creds in self.isolated_creds.values():
            self.remove_credentials(creds)

    def get_admin_creds(self):
        msg = ('If admin credentials are available tenant_isolation should be'
               ' used instead')
        raise NotImplementedError(msg)


class NotLockingAccounts(Accounts):
    """Credentials provider which always returns the first and second
    configured accounts as primary and alt users.
    This credential provider can be used in case of serial test execution
    to preserve the current behaviour of the serial tempest run.
    """

    def _unique_creds(self, cred_arg=None):
        """Verify that the configured credentials are valid and distinct """
        if self.use_default_creds:
            try:
                user = self.get_primary_creds()
                alt_user = self.get_alt_creds()
                return getattr(user, cred_arg) != getattr(alt_user, cred_arg)
            except exceptions.InvalidCredentials as ic:
                msg = "At least one of the configured credentials is " \
                      "not valid: %s" % ic.message
                raise exceptions.InvalidConfiguration(msg)
        else:
            # TODO(andreaf) Add a uniqueness check here
            return len(self.hash_dict) > 1

    def is_multi_user(self):
        return self._unique_creds('username')

    def is_multi_tenant(self):
        return self._unique_creds('tenant_id')

    def get_creds(self, id):
        try:
            # No need to sort the dict as within the same python process
            # the HASH seed won't change, so subsequent calls to keys()
            # will return the same result
            _hash = self.hash_dict.keys()[id]
        except IndexError:
            msg = 'Insufficient number of users provided'
            raise exceptions.InvalidConfiguration(msg)
        return self.hash_dict[_hash]

    def get_primary_creds(self):
        if self.isolated_creds.get('primary'):
            return self.isolated_creds.get('primary')
        if not self.use_default_creds:
            creds = self.get_creds(0)
            primary_credential = cred_provider.get_credentials(**creds)
        else:
            primary_credential = cred_provider.get_configured_credentials(
                'user')
        self.isolated_creds['primary'] = primary_credential
        return primary_credential

    def get_alt_creds(self):
        if self.isolated_creds.get('alt'):
            return self.isolated_creds.get('alt')
        if not self.use_default_creds:
            creds = self.get_creds(1)
            alt_credential = cred_provider.get_credentials(**creds)
        else:
            alt_credential = cred_provider.get_configured_credentials(
                'alt_user')
        self.isolated_creds['alt'] = alt_credential
        return alt_credential

    def clear_isolated_creds(self):
        self.isolated_creds = {}

    def get_admin_creds(self):
        return cred_provider.get_configured_credentials(
            "identity_admin", fill_in=False)
