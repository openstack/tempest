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

import mock
from oslo_concurrency.fixture import lockutils as lockutils_fixtures
from oslo_concurrency import lockutils
from oslo_config import cfg
from oslotest import mockpatch

from tempest import auth
from tempest.common import accounts
from tempest.common import cred_provider
from tempest import config
from tempest import exceptions
from tempest.services.identity.v2.json import token_client
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests import fake_http
from tempest.tests import fake_identity


class TestAccount(base.TestCase):

    def setUp(self):
        super(TestAccount, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)
        self.fake_http = fake_http.fake_httplib2(return_type=200)
        self.stubs.Set(token_client.TokenClientJSON, 'raw_request',
                       fake_identity._fake_v2_response)
        self.useFixture(lockutils_fixtures.ExternalLockFixture())
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
             'password': 'p', 'roles': ['role1', 'role2']},
            {'username': 'test_user7', 'tenant_name': 'test_tenant7',
             'password': 'p', 'roles': ['role2', 'role3']},
            {'username': 'test_user8', 'tenant_name': 'test_tenant8',
             'password': 'p', 'roles': ['role4', 'role1']},
            {'username': 'test_user9', 'tenant_name': 'test_tenant9',
             'password': 'p', 'roles': ['role1', 'role2', 'role3', 'role4']},
            {'username': 'test_user10', 'tenant_name': 'test_tenant10',
             'password': 'p', 'roles': ['role1', 'role2', 'role3', 'role4']},
            {'username': 'test_user11', 'tenant_name': 'test_tenant11',
             'password': 'p', 'roles': [cfg.CONF.identity.admin_role]},
            {'username': 'test_user12', 'tenant_name': 'test_tenant12',
             'password': 'p', 'roles': [cfg.CONF.identity.admin_role]},
            {'username': 'test_user13', 'tenant_name': 'test_tenant13',
             'password': 'p', 'resources': {'network': 'network-1'}},
            {'username': 'test_user14', 'tenant_name': 'test_tenant14',
             'password': 'p', 'roles': ['role-7', 'role-11'],
             'resources': {'network': 'network-2'}},
        ]
        self.useFixture(mockpatch.Patch(
            'tempest.common.accounts.read_accounts_yaml',
            return_value=self.test_accounts))
        cfg.CONF.set_default('test_accounts_file', 'fake_path', group='auth')
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))

    def _get_hash_list(self, accounts_list):
        hash_list = []
        for account in accounts_list:
            hash = hashlib.md5()
            hash.update(str(account))
            temp_hash = hash.hexdigest()
            hash_list.append(temp_hash)
        return hash_list

    def test_get_hash(self):
        self.stubs.Set(token_client.TokenClientJSON, 'raw_request',
                       fake_identity._fake_v2_response)
        test_account_class = accounts.Accounts('v2', 'test_name')
        hash_list = self._get_hash_list(self.test_accounts)
        test_cred_dict = self.test_accounts[3]
        test_creds = auth.get_credentials(fake_identity.FAKE_AUTH_URL,
                                          **test_cred_dict)
        results = test_account_class.get_hash(test_creds)
        self.assertEqual(hash_list[3], results)

    def test_get_hash_dict(self):
        test_account_class = accounts.Accounts('v2', 'test_name')
        hash_dict = test_account_class.get_hash_dict(self.test_accounts)
        hash_list = self._get_hash_list(self.test_accounts)
        for hash in hash_list:
            self.assertIn(hash, hash_dict['creds'].keys())
            self.assertIn(hash_dict['creds'][hash], self.test_accounts)

    def test_create_hash_file_previous_file(self):
        # Emulate the lock existing on the filesystem
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))
        with mock.patch('__builtin__.open', mock.mock_open(), create=True):
            test_account_class = accounts.Accounts('v2', 'test_name')
            res = test_account_class._create_hash_file('12345')
        self.assertFalse(res, "_create_hash_file should return False if the "
                         "pseudo-lock file already exists")

    def test_create_hash_file_no_previous_file(self):
        # Emulate the lock not existing on the filesystem
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=False))
        with mock.patch('__builtin__.open', mock.mock_open(), create=True):
            test_account_class = accounts.Accounts('v2', 'test_name')
            res = test_account_class._create_hash_file('12345')
        self.assertTrue(res, "_create_hash_file should return True if the "
                        "pseudo-lock doesn't already exist")

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_get_free_hash_no_previous_accounts(self, lock_mock):
        # Emulate no pre-existing lock
        self.useFixture(mockpatch.Patch('os.path.isdir', return_value=False))
        hash_list = self._get_hash_list(self.test_accounts)
        mkdir_mock = self.useFixture(mockpatch.Patch('os.mkdir'))
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=False))
        test_account_class = accounts.Accounts('v2', 'test_name')
        with mock.patch('__builtin__.open', mock.mock_open(),
                        create=True) as open_mock:
            test_account_class._get_free_hash(hash_list)
            lock_path = os.path.join(lockutils.get_lock_path(accounts.CONF),
                                     'test_accounts',
                                     hash_list[0])
            open_mock.assert_called_once_with(lock_path, 'w')
        mkdir_path = os.path.join(accounts.CONF.oslo_concurrency.lock_path,
                                  'test_accounts')
        mkdir_mock.mock.assert_called_once_with(mkdir_path)

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_get_free_hash_no_free_accounts(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Emulate pre-existing lock dir
        self.useFixture(mockpatch.Patch('os.path.isdir', return_value=True))
        # Emulate all lcoks in list are in use
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))
        test_account_class = accounts.Accounts('v2', 'test_name')
        with mock.patch('__builtin__.open', mock.mock_open(), create=True):
            self.assertRaises(exceptions.InvalidConfiguration,
                              test_account_class._get_free_hash, hash_list)

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_get_free_hash_some_in_use_accounts(self, lock_mock):
        # Emulate no pre-existing lock
        self.useFixture(mockpatch.Patch('os.path.isdir', return_value=True))
        hash_list = self._get_hash_list(self.test_accounts)
        test_account_class = accounts.Accounts('v2', 'test_name')

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
            lock_path = os.path.join(lockutils.get_lock_path(accounts.CONF),
                                     'test_accounts',
                                     hash_list[3])
            open_mock.assert_has_calls([mock.call(lock_path, 'w')])

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_remove_hash_last_account(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Pretend the pseudo-lock is there
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))
        # Pretend the lock dir is empty
        self.useFixture(mockpatch.Patch('os.listdir', return_value=[]))
        test_account_class = accounts.Accounts('v2', 'test_name')
        remove_mock = self.useFixture(mockpatch.Patch('os.remove'))
        rmdir_mock = self.useFixture(mockpatch.Patch('os.rmdir'))
        test_account_class.remove_hash(hash_list[2])
        hash_path = os.path.join(lockutils.get_lock_path(accounts.CONF),
                                 'test_accounts',
                                 hash_list[2])
        lock_path = os.path.join(accounts.CONF.oslo_concurrency.lock_path,
                                 'test_accounts')
        remove_mock.mock.assert_called_once_with(hash_path)
        rmdir_mock.mock.assert_called_once_with(lock_path)

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_remove_hash_not_last_account(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Pretend the pseudo-lock is there
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))
        # Pretend the lock dir is empty
        self.useFixture(mockpatch.Patch('os.listdir', return_value=[
            hash_list[1], hash_list[4]]))
        test_account_class = accounts.Accounts('v2', 'test_name')
        remove_mock = self.useFixture(mockpatch.Patch('os.remove'))
        rmdir_mock = self.useFixture(mockpatch.Patch('os.rmdir'))
        test_account_class.remove_hash(hash_list[2])
        hash_path = os.path.join(lockutils.get_lock_path(accounts.CONF),
                                 'test_accounts',
                                 hash_list[2])
        remove_mock.mock.assert_called_once_with(hash_path)
        rmdir_mock.mock.assert_not_called()

    def test_is_multi_user(self):
        test_accounts_class = accounts.Accounts('v2', 'test_name')
        self.assertTrue(test_accounts_class.is_multi_user())

    def test_is_not_multi_user(self):
        self.test_accounts = [self.test_accounts[0]]
        self.useFixture(mockpatch.Patch(
            'tempest.common.accounts.read_accounts_yaml',
            return_value=self.test_accounts))
        test_accounts_class = accounts.Accounts('v2', 'test_name')
        self.assertFalse(test_accounts_class.is_multi_user())

    def test__get_creds_by_roles_one_role(self):
        self.useFixture(mockpatch.Patch(
            'tempest.common.accounts.read_accounts_yaml',
            return_value=self.test_accounts))
        test_accounts_class = accounts.Accounts('v2', 'test_name')
        hashes = test_accounts_class.hash_dict['roles']['role4']
        temp_hash = hashes[0]
        get_free_hash_mock = self.useFixture(mockpatch.PatchObject(
            test_accounts_class, '_get_free_hash', return_value=temp_hash))
        # Test a single role returns all matching roles
        test_accounts_class._get_creds(roles=['role4'])
        calls = get_free_hash_mock.mock.mock_calls
        self.assertEqual(len(calls), 1)
        args = calls[0][1][0]
        for i in hashes:
            self.assertIn(i, args)

    def test__get_creds_by_roles_list_role(self):
        self.useFixture(mockpatch.Patch(
            'tempest.common.accounts.read_accounts_yaml',
            return_value=self.test_accounts))
        test_accounts_class = accounts.Accounts('v2', 'test_name')
        hashes = test_accounts_class.hash_dict['roles']['role4']
        hashes2 = test_accounts_class.hash_dict['roles']['role2']
        hashes = list(set(hashes) & set(hashes2))
        temp_hash = hashes[0]
        get_free_hash_mock = self.useFixture(mockpatch.PatchObject(
            test_accounts_class, '_get_free_hash', return_value=temp_hash))
        # Test an intersection of multiple roles
        test_accounts_class._get_creds(roles=['role2', 'role4'])
        calls = get_free_hash_mock.mock.mock_calls
        self.assertEqual(len(calls), 1)
        args = calls[0][1][0]
        for i in hashes:
            self.assertIn(i, args)

    def test__get_creds_by_roles_no_admin(self):
        self.useFixture(mockpatch.Patch(
            'tempest.common.accounts.read_accounts_yaml',
            return_value=self.test_accounts))
        test_accounts_class = accounts.Accounts('v2', 'test_name')
        hashes = test_accounts_class.hash_dict['creds'].keys()
        admin_hashes = test_accounts_class.hash_dict['roles'][
            cfg.CONF.identity.admin_role]
        temp_hash = hashes[0]
        get_free_hash_mock = self.useFixture(mockpatch.PatchObject(
            test_accounts_class, '_get_free_hash', return_value=temp_hash))
        # Test an intersection of multiple roles
        test_accounts_class._get_creds()
        calls = get_free_hash_mock.mock.mock_calls
        self.assertEqual(len(calls), 1)
        args = calls[0][1][0]
        self.assertEqual(len(args), 12)
        for i in admin_hashes:
            self.assertNotIn(i, args)

    def test_networks_returned_with_creds(self):
        self.useFixture(mockpatch.Patch(
            'tempest.common.accounts.read_accounts_yaml',
            return_value=self.test_accounts))
        test_accounts_class = accounts.Accounts('v2', 'test_name')
        with mock.patch('tempest.services.compute.json.networks_client.'
                        'NetworksClientJSON.list_networks',
                        return_value=[{'name': 'network-2', 'id': 'fake-id'}]):
            creds = test_accounts_class.get_creds_by_roles(['role-7'])
        self.assertTrue(isinstance(creds, cred_provider.TestResources))
        network = creds.network
        self.assertIsNotNone(network)
        self.assertIn('name', network)
        self.assertIn('id', network)
        self.assertEqual('fake-id', network['id'])
        self.assertEqual('network-2', network['name'])


class TestNotLockingAccount(base.TestCase):

    def setUp(self):
        super(TestNotLockingAccount, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)
        self.useFixture(lockutils_fixtures.ExternalLockFixture())
        self.test_accounts = [
            {'username': 'test_user1', 'tenant_name': 'test_tenant1',
             'password': 'p'},
            {'username': 'test_user2', 'tenant_name': 'test_tenant2',
             'password': 'p'},
            {'username': 'test_user3', 'tenant_name': 'test_tenant3',
             'password': 'p'},
        ]
        self.useFixture(mockpatch.Patch(
            'tempest.common.accounts.read_accounts_yaml',
            return_value=self.test_accounts))
        cfg.CONF.set_default('test_accounts_file', '', group='auth')
        self.useFixture(mockpatch.Patch('os.path.isfile', return_value=True))

    def test_get_creds_roles_nonlocking_invalid(self):
        test_accounts_class = accounts.NotLockingAccounts('v2', 'test_name')
        self.assertRaises(exceptions.InvalidConfiguration,
                          test_accounts_class.get_creds_by_roles,
                          ['fake_role'])
