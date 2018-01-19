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
import shutil

import mock
import six
import testtools

import fixtures
from oslo_concurrency.fixture import lockutils as lockutils_fixtures
from oslo_config import cfg

from tempest import config
from tempest.lib import auth
from tempest.lib.common import cred_provider
from tempest.lib.common import preprov_creds
from tempest.lib import exceptions as lib_exc
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests.lib import fake_identity
from tempest.tests.lib.services import registry_fixture


class TestPreProvisionedCredentials(base.TestCase):

    fixed_params = {'name': 'test class',
                    'identity_version': 'v2',
                    'identity_uri': 'fake_uri',
                    'test_accounts_file': 'fake_accounts_file',
                    'accounts_lock_dir': 'fake_locks_dir',
                    'admin_role': 'admin',
                    'object_storage_operator_role': 'operator',
                    'object_storage_reseller_admin_role': 'reseller'}

    identity_response = fake_identity._fake_v2_response
    token_client = ('tempest.lib.services.identity.v2.token_client'
                    '.TokenClient.raw_request')

    @classmethod
    def _fake_accounts(cls, admin_role):
        return [
            {'username': 'test_user1', 'tenant_name': 'test_tenant1',
             'password': 'p'},
            {'username': 'test_user2', 'project_name': 'test_tenant2',
             'password': 'p'},
            {'username': 'test_user3', 'tenant_name': 'test_tenant3',
             'password': 'p'},
            {'username': 'test_user4', 'project_name': 'test_tenant4',
             'password': 'p'},
            {'username': 'test_user5', 'tenant_name': 'test_tenant5',
             'password': 'p'},
            {'username': 'test_user6', 'project_name': 'test_tenant6',
             'password': 'p', 'roles': ['role1', 'role2']},
            {'username': 'test_user7', 'tenant_name': 'test_tenant7',
             'password': 'p', 'roles': ['role2', 'role3']},
            {'username': 'test_user8', 'project_name': 'test_tenant8',
             'password': 'p', 'roles': ['role4', 'role1']},
            {'username': 'test_user9', 'tenant_name': 'test_tenant9',
             'password': 'p', 'roles': ['role1', 'role2', 'role3', 'role4']},
            {'username': 'test_user10', 'project_name': 'test_tenant10',
             'password': 'p', 'roles': ['role1', 'role2', 'role3', 'role4']},
            {'username': 'test_admin1', 'tenant_name': 'test_tenant11',
             'password': 'p', 'roles': [admin_role]},
            {'username': 'test_admin2', 'project_name': 'test_tenant12',
             'password': 'p', 'roles': [admin_role]},
            {'username': 'test_admin3', 'project_name': 'test_tenant13',
             'password': 'p', 'types': ['admin']}]

    def setUp(self):
        super(TestPreProvisionedCredentials, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        self.patch(self.token_client, side_effect=self.identity_response)
        self.useFixture(lockutils_fixtures.ExternalLockFixture())
        self.test_accounts = self._fake_accounts(cfg.CONF.identity.admin_role)
        self.accounts_mock = self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.preprov_creds.read_accounts_yaml',
            return_value=self.test_accounts))
        self.useFixture(fixtures.MockPatch(
            'os.path.isfile', return_value=True))
        # Make sure we leave the registry clean
        self.useFixture(registry_fixture.RegistryFixture())

    def tearDown(self):
        super(TestPreProvisionedCredentials, self).tearDown()
        shutil.rmtree(self.fixed_params['accounts_lock_dir'],
                      ignore_errors=True)

    def _get_hash_list(self, accounts_list):
        hash_list = []
        hash_fields = (
            preprov_creds.PreProvisionedCredentialProvider.HASH_CRED_FIELDS)
        for account in accounts_list:
            hash = hashlib.md5()
            account_for_hash = dict((k, v) for (k, v) in account.items()
                                    if k in hash_fields)
            hash.update(six.text_type(account_for_hash).encode('utf-8'))
            temp_hash = hash.hexdigest()
            hash_list.append(temp_hash)
        return hash_list

    def test_get_hash(self):
        # Test with all accounts to make sure we try all combinations
        # and hide no race conditions
        hash_index = 0
        for test_cred_dict in self.test_accounts:
            test_account_class = (
                preprov_creds.PreProvisionedCredentialProvider(
                    **self.fixed_params))
            hash_list = self._get_hash_list(self.test_accounts)
            test_creds = auth.get_credentials(
                fake_identity.FAKE_AUTH_URL,
                identity_version=self.fixed_params['identity_version'],
                **test_cred_dict)
            results = test_account_class.get_hash(test_creds)
            self.assertEqual(hash_list[hash_index], results)
            hash_index += 1

    def test_get_hash_dict(self):
        test_account_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        hash_dict = test_account_class.get_hash_dict(
            self.test_accounts, self.fixed_params['admin_role'])
        hash_list = self._get_hash_list(self.test_accounts)
        for hash in hash_list:
            self.assertIn(hash, hash_dict['creds'].keys())
            self.assertIn(hash_dict['creds'][hash], self.test_accounts)

    def test_create_hash_file_previous_file(self):
        # Emulate the lock existing on the filesystem
        self.useFixture(fixtures.MockPatch(
            'os.path.isfile', return_value=True))
        with mock.patch('six.moves.builtins.open', mock.mock_open(),
                        create=True):
            test_account_class = (
                preprov_creds.PreProvisionedCredentialProvider(
                    **self.fixed_params))
            res = test_account_class._create_hash_file('12345')
        self.assertFalse(res, "_create_hash_file should return False if the "
                         "pseudo-lock file already exists")

    def test_create_hash_file_no_previous_file(self):
        # Emulate the lock not existing on the filesystem
        self.useFixture(fixtures.MockPatch(
            'os.path.isfile', return_value=False))
        with mock.patch('six.moves.builtins.open', mock.mock_open(),
                        create=True):
            test_account_class = (
                preprov_creds.PreProvisionedCredentialProvider(
                    **self.fixed_params))
            res = test_account_class._create_hash_file('12345')
        self.assertTrue(res, "_create_hash_file should return True if the "
                        "pseudo-lock doesn't already exist")

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_get_free_hash_no_previous_accounts(self, lock_mock):
        # Emulate no pre-existing lock
        self.useFixture(fixtures.MockPatch(
            'os.path.isdir', return_value=False))
        hash_list = self._get_hash_list(self.test_accounts)
        mkdir_mock = self.useFixture(fixtures.MockPatch('os.mkdir'))
        self.useFixture(fixtures.MockPatch(
            'os.path.isfile', return_value=False))
        test_account_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        with mock.patch('six.moves.builtins.open', mock.mock_open(),
                        create=True) as open_mock:
            test_account_class._get_free_hash(hash_list)
            lock_path = os.path.join(self.fixed_params['accounts_lock_dir'],
                                     hash_list[0])
            open_mock.assert_called_once_with(lock_path, 'w')
        mkdir_path = os.path.join(self.fixed_params['accounts_lock_dir'])
        mkdir_mock.mock.assert_called_once_with(mkdir_path)

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_get_free_hash_no_free_accounts(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Emulate pre-existing lock dir
        self.useFixture(fixtures.MockPatch('os.path.isdir', return_value=True))
        # Emulate all locks in list are in use
        self.useFixture(fixtures.MockPatch(
            'os.path.isfile', return_value=True))
        test_account_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        with mock.patch('six.moves.builtins.open', mock.mock_open(),
                        create=True):
            self.assertRaises(lib_exc.InvalidCredentials,
                              test_account_class._get_free_hash, hash_list)

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_get_free_hash_some_in_use_accounts(self, lock_mock):
        # Emulate no pre-existing lock
        self.useFixture(fixtures.MockPatch('os.path.isdir', return_value=True))
        hash_list = self._get_hash_list(self.test_accounts)
        test_account_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)

        def _fake_is_file(path):
            # Fake isfile() to return that the path exists unless a specific
            # hash is in the path
            if hash_list[3] in path:
                return False
            return True

        self.patchobject(os.path, 'isfile', _fake_is_file)
        with mock.patch('six.moves.builtins.open', mock.mock_open(),
                        create=True) as open_mock:
            test_account_class._get_free_hash(hash_list)
            lock_path = os.path.join(self.fixed_params['accounts_lock_dir'],
                                     hash_list[3])
            open_mock.assert_has_calls([mock.call(lock_path, 'w')])

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_remove_hash_last_account(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Pretend the pseudo-lock is there
        self.useFixture(
            fixtures.MockPatch('os.path.isfile', return_value=True))
        # Pretend the lock dir is empty
        self.useFixture(fixtures.MockPatch('os.listdir', return_value=[]))
        test_account_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        remove_mock = self.useFixture(fixtures.MockPatch('os.remove'))
        rmdir_mock = self.useFixture(fixtures.MockPatch('os.rmdir'))
        test_account_class.remove_hash(hash_list[2])
        hash_path = os.path.join(self.fixed_params['accounts_lock_dir'],
                                 hash_list[2])
        lock_path = self.fixed_params['accounts_lock_dir']
        remove_mock.mock.assert_called_once_with(hash_path)
        rmdir_mock.mock.assert_called_once_with(lock_path)

    @mock.patch('oslo_concurrency.lockutils.lock')
    def test_remove_hash_not_last_account(self, lock_mock):
        hash_list = self._get_hash_list(self.test_accounts)
        # Pretend the pseudo-lock is there
        self.useFixture(fixtures.MockPatch(
            'os.path.isfile', return_value=True))
        # Pretend the lock dir is empty
        self.useFixture(fixtures.MockPatch('os.listdir', return_value=[
            hash_list[1], hash_list[4]]))
        test_account_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        remove_mock = self.useFixture(fixtures.MockPatch('os.remove'))
        rmdir_mock = self.useFixture(fixtures.MockPatch('os.rmdir'))
        test_account_class.remove_hash(hash_list[2])
        hash_path = os.path.join(self.fixed_params['accounts_lock_dir'],
                                 hash_list[2])
        remove_mock.mock.assert_called_once_with(hash_path)
        rmdir_mock.mock.assert_not_called()

    def test_is_multi_user(self):
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        self.assertTrue(test_accounts_class.is_multi_user())

    def test_is_not_multi_user(self):
        self.test_accounts = [self.test_accounts[0]]
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.preprov_creds.read_accounts_yaml',
            return_value=self.test_accounts))
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        self.assertFalse(test_accounts_class.is_multi_user())

    def test__get_creds_by_roles_one_role(self):
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        hashes = test_accounts_class.hash_dict['roles']['role4']
        temp_hash = hashes[0]
        get_free_hash_mock = self.useFixture(fixtures.MockPatchObject(
            test_accounts_class, '_get_free_hash', return_value=temp_hash))
        # Test a single role returns all matching roles
        test_accounts_class._get_creds(roles=['role4'])
        calls = get_free_hash_mock.mock.mock_calls
        self.assertEqual(len(calls), 1)
        args = calls[0][1][0]
        for i in hashes:
            self.assertIn(i, args)

    def test__get_creds_by_roles_list_role(self):
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        hashes = test_accounts_class.hash_dict['roles']['role4']
        hashes2 = test_accounts_class.hash_dict['roles']['role2']
        hashes = list(set(hashes) & set(hashes2))
        temp_hash = hashes[0]
        get_free_hash_mock = self.useFixture(fixtures.MockPatchObject(
            test_accounts_class, '_get_free_hash', return_value=temp_hash))
        # Test an intersection of multiple roles
        test_accounts_class._get_creds(roles=['role2', 'role4'])
        calls = get_free_hash_mock.mock.mock_calls
        self.assertEqual(len(calls), 1)
        args = calls[0][1][0]
        for i in hashes:
            self.assertIn(i, args)

    def test__get_creds_by_roles_no_admin(self):
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        hashes = list(test_accounts_class.hash_dict['creds'].keys())
        admin_hashes = test_accounts_class.hash_dict['roles'][
            cfg.CONF.identity.admin_role]
        temp_hash = hashes[0]
        get_free_hash_mock = self.useFixture(fixtures.MockPatchObject(
            test_accounts_class, '_get_free_hash', return_value=temp_hash))
        # Test an intersection of multiple roles
        test_accounts_class._get_creds()
        calls = get_free_hash_mock.mock.mock_calls
        self.assertEqual(len(calls), 1)
        args = calls[0][1][0]
        self.assertEqual(len(args), 10)
        for i in admin_hashes:
            self.assertNotIn(i, args)

    def test_networks_returned_with_creds(self):
        test_accounts = [
            {'username': 'test_user13', 'tenant_name': 'test_tenant13',
             'password': 'p', 'resources': {'network': 'network-1'}},
            {'username': 'test_user14', 'tenant_name': 'test_tenant14',
             'password': 'p', 'roles': ['role-7', 'role-11'],
             'resources': {'network': 'network-2'}}]
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.preprov_creds.read_accounts_yaml',
            return_value=test_accounts))
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        with mock.patch('tempest.lib.services.network.networks_client.'
                        'NetworksClient.list_networks',
                        return_value={'networks': [{'name': 'network-2',
                                                    'id': 'fake-id',
                                                    'label': 'network-2'}]}):
            creds = test_accounts_class.get_creds_by_roles(['role-7'])
        self.assertIsInstance(creds, cred_provider.TestResources)
        network = creds.network
        self.assertIsNotNone(network)
        self.assertIn('name', network)
        self.assertIn('id', network)
        self.assertEqual('fake-id', network['id'])
        self.assertEqual('network-2', network['name'])

    def test_get_primary_creds(self):
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        primary_creds = test_accounts_class.get_primary_creds()
        self.assertNotIn('test_admin', primary_creds.username)

    def test_get_primary_creds_none_available(self):
        admin_accounts = [x for x in self.test_accounts if 'test_admin'
                          in x['username']]
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.preprov_creds.read_accounts_yaml',
            return_value=admin_accounts))
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        with testtools.ExpectedException(lib_exc.InvalidCredentials):
            # Get one more
            test_accounts_class.get_primary_creds()

    def test_get_alt_creds(self):
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        alt_creds = test_accounts_class.get_alt_creds()
        self.assertNotIn('test_admin', alt_creds.username)

    def test_get_alt_creds_none_available(self):
        admin_accounts = [x for x in self.test_accounts if 'test_admin'
                          in x['username']]
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.preprov_creds.read_accounts_yaml',
            return_value=admin_accounts))
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        with testtools.ExpectedException(lib_exc.InvalidCredentials):
            # Get one more
            test_accounts_class.get_alt_creds()

    def test_get_admin_creds(self):
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        admin_creds = test_accounts_class.get_admin_creds()
        self.assertIn('test_admin', admin_creds.username)

    def test_get_admin_creds_by_type(self):
        test_accounts = [
            {'username': 'test_user10', 'project_name': 'test_tenant10',
             'password': 'p', 'roles': ['role1', 'role2', 'role3', 'role4']},
            {'username': 'test_admin1', 'tenant_name': 'test_tenant11',
             'password': 'p', 'types': ['admin']}]
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.preprov_creds.read_accounts_yaml',
            return_value=test_accounts))
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        admin_creds = test_accounts_class.get_admin_creds()
        self.assertIn('test_admin', admin_creds.username)

    def test_get_admin_creds_by_role(self):
        test_accounts = [
            {'username': 'test_user10', 'project_name': 'test_tenant10',
             'password': 'p', 'roles': ['role1', 'role2', 'role3', 'role4']},
            {'username': 'test_admin1', 'tenant_name': 'test_tenant11',
             'password': 'p', 'roles': [cfg.CONF.identity.admin_role]}]
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.preprov_creds.read_accounts_yaml',
            return_value=test_accounts))
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        admin_creds = test_accounts_class.get_admin_creds()
        self.assertIn('test_admin', admin_creds.username)

    def test_get_admin_creds_none_available(self):
        non_admin_accounts = [x for x in self.test_accounts if 'test_admin'
                              not in x['username']]
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.preprov_creds.read_accounts_yaml',
            return_value=non_admin_accounts))
        test_accounts_class = preprov_creds.PreProvisionedCredentialProvider(
            **self.fixed_params)
        with testtools.ExpectedException(lib_exc.InvalidCredentials):
            # Get one more
            test_accounts_class.get_admin_creds()


class TestPreProvisionedCredentialsV3(TestPreProvisionedCredentials):

    fixed_params = {'name': 'test class',
                    'identity_version': 'v3',
                    'identity_uri': 'fake_uri',
                    'test_accounts_file': 'fake_accounts_file',
                    'accounts_lock_dir': 'fake_locks_dir_v3',
                    'admin_role': 'admin',
                    'object_storage_operator_role': 'operator',
                    'object_storage_reseller_admin_role': 'reseller'}

    identity_response = fake_identity._fake_v3_response
    token_client = ('tempest.lib.services.identity.v3.token_client'
                    '.V3TokenClient.raw_request')

    @classmethod
    def _fake_accounts(cls, admin_role):
        return [
            {'username': 'test_user1', 'project_name': 'test_project1',
             'domain_name': 'domain', 'password': 'p'},
            {'username': 'test_user2', 'project_name': 'test_project2',
             'domain_name': 'domain', 'password': 'p'},
            {'username': 'test_user3', 'project_name': 'test_project3',
             'domain_name': 'domain', 'password': 'p'},
            {'username': 'test_user4', 'project_name': 'test_project4',
             'domain_name': 'domain', 'password': 'p'},
            {'username': 'test_user5', 'project_name': 'test_project5',
             'domain_name': 'domain', 'password': 'p'},
            {'username': 'test_user6', 'project_name': 'test_project6',
             'domain_name': 'domain', 'password': 'p',
             'roles': ['role1', 'role2']},
            {'username': 'test_user7', 'project_name': 'test_project7',
             'domain_name': 'domain', 'password': 'p',
             'roles': ['role2', 'role3']},
            {'username': 'test_user8', 'project_name': 'test_project8',
             'domain_name': 'domain', 'password': 'p',
             'roles': ['role4', 'role1']},
            {'username': 'test_user9', 'project_name': 'test_project9',
             'domain_name': 'domain', 'password': 'p',
             'roles': ['role1', 'role2', 'role3', 'role4']},
            {'username': 'test_user10', 'project_name': 'test_project10',
             'domain_name': 'domain', 'password': 'p',
             'roles': ['role1', 'role2', 'role3', 'role4']},
            {'username': 'test_admin1', 'project_name': 'test_project11',
             'domain_name': 'domain', 'password': 'p', 'roles': [admin_role]},
            {'username': 'test_admin2', 'project_name': 'test_project12',
             'domain_name': 'domain', 'password': 'p', 'roles': [admin_role]},
            {'username': 'test_admin3', 'project_name': 'test_tenant13',
             'domain_name': 'domain', 'password': 'p', 'types': ['admin']}]
