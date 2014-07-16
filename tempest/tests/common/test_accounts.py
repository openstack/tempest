# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import tempfile

import mock
from oslo.config import cfg
from oslotest import mockpatch

from tempest import auth
from tempest.common import accounts
from tempest.common import http
from tempest import config
from tempest import exceptions
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests import fake_identity


class TestAccount(base.TestCase):

    def setUp(self):
        super(TestAccount, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)
        self.temp_dir = tempfile.mkdtemp()
        cfg.CONF.set_default('lock_path', self.temp_dir)
        self.addCleanup(os.rmdir, self.temp_dir)
        self.test_accounts = [
            {'username': 'test_user1', 'tenant_name': 'test_tenant1',
             'password': 'p'},
            {'username': 'test_user2', 'tenant_name': 'test_tenant2',
             'password': 'p'},
            {'username': 'test_user3', 'tenant_name': 'test_tenant3',
             'password': 'p'},
            {'username': 'test_user4', 'tenant_name': 'test_tenant4',
             'password': 'p'},
            {'username': 'test_user5', 'tenant_name': 'test_tenant5',
             'password': 'p'},
            {'username': 'test_user6', 'tenant_name': 'test_tenant6',
             'password': 'p'},
        ]
        self.useFixture(mockpatch.Patch(
            'tempest.common.accounts.read_accounts_yaml',
            return_value=self.test_accounts))
        cfg.CONF.set_default('test_accounts_file', '', group='auth')

    def _get_hash_list(self, accounts_list):
        hash_list = []
        for account in accounts_list:
            hash = hashlib.md5()
            hash.update(str(account))
            hash_list.append(hash.hexdigest())
        return hash_list

    def test_get_hash(self):
        self.stubs.Set(http.ClosingHttp, 'request',
                       fake_identity._fake_v2_response)
        test_account_class = accounts.Accounts('test_name')
        hash_list = self._get_hash_list(self.test_accounts)
        test_cred_dict = self.test_accounts[3]
        test_creds = auth.get_credentials(**test_cred_dict)
        results = test_account_class.get_hash(test_creds)
        self.assertEqual(hash_list[3], results)

    def test_get_hash_dict(self):
        test_account_class = accounts.Accounts('test_name')
        hash_dict = test_account_class.get_hash_dict(self.test_accounts)
        hash_list = self._get_hash_list(self.test_accounts)
        for hash in hash_list:
            self.assertIn(hash, hash_dict.keys())
            self.assertIn(hash_dict[hash], self.test_accounts)

    def test_create_hash_file_previous_file(self):
        # Emulate the lock existing on the filesystem
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))
        with mock.patch('__builtin__.open', mock.mock_open(), create=True):
            test_account_class = accounts.Accounts('test_name')
            res = test_account_class._create_hash_file('12345')
        self.assertFalse(res, "_create_hash_file should return False if the "
                         "pseudo-lock file already exists")

    def test_create_hash_file_no_previous_file(self):
        # Emulate the lock not existing on the filesystem
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=False))
        with mock.patch('__builtin__.open', mock.mock_open(), create=True):
            test_account_class = accounts.Accounts('test_name')
            res = test_account_class._create_hash_file('12345')
        self.assertTrue(res, "_create_hash_file should return True if the "
                        "pseudo-lock doesn't already exist")

    @mock.patch('tempest.openstack.common.lockutils.lock')
    def test_get_free_hash_no_previous_accounts(self, lock_mock):
        # Emulate no pre-existing lock
        self.useFixture(mockpatch.Patch('os.path.isdir', return_value=False))
        hash_list = self._get_hash_list(self.test_accounts)
        mkdir_mock = self.useFixture(mockpatch.Patch('os.mkdir'))
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=False))
        test_account_class = accounts.Accounts('test_name')
        with mock.patch('__builtin__.open', mock.mock_open(),
                        create=True) as open_mock:
            test_account_class._get_free_hash(hash_list)
            lock_path = os.path.join(accounts.CONF.lock_path, 'test_accounts',
                                     hash_list[0])
            open_mock.assert_called_once_with(lock_path, 'w')
        mkdir_path = os.path.join(accounts.CONF.lock_path, 'test_accounts')
        mkdir_mock.mock.assert_called_once_with(mkdir_path)

    @mock.patch('tempest.openstack.common.lockutils.lock')
    def test_get_free_hash_no_free_accounts(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Emulate pre-existing lock dir
        self.useFixture(mockpatch.Patch('os.path.isdir', return_value=True))
        # Emulate all lcoks in list are in use
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))
        test_account_class = accounts.Accounts('test_name')
        self.assertRaises(exceptions.InvalidConfiguration,
                          test_account_class._get_free_hash, hash_list)

    @mock.patch('tempest.openstack.common.lockutils.lock')
    def test_get_free_hash_some_in_use_accounts(self, lock_mock):
        # Emulate no pre-existing lock
        self.useFixture(mockpatch.Patch('os.path.isdir', return_value=True))
        hash_list = self._get_hash_list(self.test_accounts)
        test_account_class = accounts.Accounts('test_name')

        def _fake_is_file(path):
            # Fake isfile() to return that the path exists unless a specific
            # hash is in the path
            if hash_list[3] in path:
                return False
            return True

        self.stubs.Set(os.path, 'isfile', _fake_is_file)
        with mock.patch('__builtin__.open', mock.mock_open(),
                        create=True) as open_mock:
            test_account_class._get_free_hash(hash_list)
            lock_path = os.path.join(accounts.CONF.lock_path, 'test_accounts',
                                     hash_list[3])
            open_mock.assert_called_once_with(lock_path, 'w')

    @mock.patch('tempest.openstack.common.lockutils.lock')
    def test_remove_hash_last_account(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Pretend the pseudo-lock is there
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))
        # Pretend the lock dir is empty
        self.useFixture(mockpatch.Patch('os.listdir', return_value=[]))
        test_account_class = accounts.Accounts('test_name')
        remove_mock = self.useFixture(mockpatch.Patch('os.remove'))
        rmdir_mock = self.useFixture(mockpatch.Patch('os.rmdir'))
        test_account_class.remove_hash(hash_list[2])
        hash_path = os.path.join(accounts.CONF.lock_path, 'test_accounts',
                                 hash_list[2])
        lock_path = os.path.join(accounts.CONF.lock_path, 'test_accounts')
        remove_mock.mock.assert_called_once_with(hash_path)
        rmdir_mock.mock.assert_called_once_with(lock_path)

    @mock.patch('tempest.openstack.common.lockutils.lock')
    def test_remove_hash_not_last_account(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Pretend the pseudo-lock is there
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))
        # Pretend the lock dir is empty
        self.useFixture(mockpatch.Patch('os.listdir', return_value=[
            hash_list[1], hash_list[4]]))
        test_account_class = accounts.Accounts('test_name')
        remove_mock = self.useFixture(mockpatch.Patch('os.remove'))
        rmdir_mock = self.useFixture(mockpatch.Patch('os.rmdir'))
        test_account_class.remove_hash(hash_list[2])
        hash_path = os.path.join(accounts.CONF.lock_path, 'test_accounts',
                                 hash_list[2])
        remove_mock.mock.assert_called_once_with(hash_path)
        rmdir_mock.mock.assert_not_called()
