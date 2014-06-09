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

from tempest import auth
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
        accounts = read_accounts_yaml(CONF.auth.test_accounts_file)
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

    def _create_hash_file(self, hash):
        path = os.path.join(os.path.join(self.accounts_dir, hash))
        if not os.path.isfile(path):
            open(path, 'w').close()
            return True
        return False

    @lockutils.synchronized('test_accounts_io', external=True)
    def _get_free_hash(self, hashes):
        if not os.path.isdir(self.accounts_dir):
            os.mkdir(self.accounts_dir)
            # Create File from first hash (since none are in use)
            self._create_hash_file(hashes[0])
            return hashes[0]
        for hash in hashes:
            res = self._create_hash_file(hash)
            if res:
                return hash
        msg = 'Insufficient number of users provided'
        raise exceptions.InvalidConfiguration(msg)

    def _get_creds(self):
        free_hash = self._get_free_hash(self.hashes.keys())
        return self.hash_dict[free_hash]

    @lockutils.synchronized('test_accounts_io', external=True)
    def remove_hash(self, hash):
        hash_path = os.path.join(self.accounts_dir, hash)
        if not os.path.isfile(hash_path):
            LOG.warning('Expected an account lock file %s to remove, but '
                        'one did not exist')
        else:
            os.remove(hash_path)
            if not os.listdir(self.accounts_dir):
                os.rmdir(self.accounts_dir)

    def get_hash(self, creds):
        for hash in self.hash_dict:
            # NOTE(mtreinish) Assuming with v3 that username, tenant, password
            # is unique enough
            cred_dict = {
                'username': creds.username,
                'tenant_name': creds.tenant_name,
                'password': creds.password
            }
            if self.hash_dict[hash] == cred_dict:
                return hash
        raise AttributeError('Invalid credentials %s' % creds)

    def remove_credentials(self, creds):
        hash = self.get_hash(creds)
        self.remove_hash(hash, self.accounts_dir)

    def get_primary_creds(self):
        if self.credentials.get('primary'):
            return self.credentials.get('primary')
        creds = self._get_creds()
        primary_credential = auth.get_credentials(**creds)
        self.credentials['primary'] = primary_credential
        return primary_credential

    def get_alt_creds(self):
        if self.credentials.get('alt'):
            return self.credentials.get('alt')
        creds = self._get_creds()
        alt_credential = auth.get_credentials(**creds)
        self.credentials['alt'] = alt_credential
        return alt_credential

    def clear_isolated_creds(self):
        for creds in self.credentials.values():
            self.remove_credentials(creds)

    def get_admin_creds(self):
        msg = ('If admin credentials are available tenant_isolation should be'
               ' used instead')
        raise NotImplementedError(msg)
