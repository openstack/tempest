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

from oslo_concurrency import lockutils
from oslo_log import log as logging
import six
import yaml

from tempest import clients
from tempest.common import cred_provider
from tempest.common import fixed_network
from tempest import exceptions
from tempest.lib import auth
from tempest.lib import exceptions as lib_exc

LOG = logging.getLogger(__name__)


def read_accounts_yaml(path):
    try:
        with open(path, 'r') as yaml_file:
            accounts = yaml.load(yaml_file)
    except IOError:
        raise exceptions.InvalidConfiguration(
            'The path for the test accounts file: %s '
            'could not be found' % path)
    return accounts


class PreProvisionedCredentialProvider(cred_provider.CredentialProvider):

    def __init__(self, identity_version, test_accounts_file,
                 accounts_lock_dir, name=None, credentials_domain=None,
                 admin_role=None, object_storage_operator_role=None,
                 object_storage_reseller_admin_role=None):
        """Credentials provider using pre-provisioned accounts

        This credentials provider loads the details of pre-provisioned
        accounts from a YAML file, in the format specified by
        `etc/accounts.yaml.sample`. It locks accounts while in use, using the
        external locking mechanism, allowing for multiple python processes
        to share a single account file, and thus running tests in parallel.

        The accounts_lock_dir must be generated using `lockutils.get_lock_path`
        from the oslo.concurrency library. For instance:

            accounts_lock_dir = os.path.join(lockutils.get_lock_path(CONF),
                                             'test_accounts')

        Role names for object storage are optional as long as the
        `operator` and `reseller_admin` credential types are not used in the
        accounts file.

        :param identity_version: identity version of the credentials
        :param admin_role: name of the admin role
        :param test_accounts_file: path to the accounts YAML file
        :param accounts_lock_dir: the directory for external locking
        :param name: name of the hash file (optional)
        :param credentials_domain: name of the domain credentials belong to
                                   (if no domain is configured)
        :param object_storage_operator_role: name of the role
        :param object_storage_reseller_admin_role: name of the role
        """
        super(PreProvisionedCredentialProvider, self).__init__(
            identity_version=identity_version, name=name,
            admin_role=admin_role, credentials_domain=credentials_domain)
        self.test_accounts_file = test_accounts_file
        if test_accounts_file:
            accounts = read_accounts_yaml(self.test_accounts_file)
            self.use_default_creds = False
        else:
            accounts = {}
            self.use_default_creds = True
        self.hash_dict = self.get_hash_dict(
            accounts, admin_role, object_storage_operator_role,
            object_storage_reseller_admin_role)
        self.accounts_dir = accounts_lock_dir
        self._creds = {}

    @classmethod
    def _append_role(cls, role, account_hash, hash_dict):
        if role in hash_dict['roles']:
            hash_dict['roles'][role].append(account_hash)
        else:
            hash_dict['roles'][role] = [account_hash]
        return hash_dict

    @classmethod
    def get_hash_dict(cls, accounts, admin_role,
                      object_storage_operator_role=None,
                      object_storage_reseller_admin_role=None):
        hash_dict = {'roles': {}, 'creds': {}, 'networks': {}}
        # Loop over the accounts read from the yaml file
        for account in accounts:
            roles = []
            types = []
            resources = []
            if 'roles' in account:
                roles = account.pop('roles')
            if 'types' in account:
                types = account.pop('types')
            if 'resources' in account:
                resources = account.pop('resources')
            temp_hash = hashlib.md5()
            temp_hash.update(six.text_type(account).encode('utf-8'))
            temp_hash_key = temp_hash.hexdigest()
            hash_dict['creds'][temp_hash_key] = account
            for role in roles:
                hash_dict = cls._append_role(role, temp_hash_key,
                                             hash_dict)
            # If types are set for the account append the matching role
            # subdict with the hash
            for type in types:
                if type == 'admin':
                    hash_dict = cls._append_role(admin_role, temp_hash_key,
                                                 hash_dict)
                elif type == 'operator':
                    if object_storage_operator_role:
                        hash_dict = cls._append_role(
                            object_storage_operator_role, temp_hash_key,
                            hash_dict)
                    else:
                        msg = ("Type 'operator' configured, but no "
                               "object_storage_operator_role specified")
                        raise lib_exc.InvalidCredentials(msg)
                elif type == 'reseller_admin':
                    if object_storage_reseller_admin_role:
                        hash_dict = cls._append_role(
                            object_storage_reseller_admin_role,
                            temp_hash_key,
                            hash_dict)
                    else:
                        msg = ("Type 'reseller_admin' configured, but no "
                               "object_storage_reseller_admin_role specified")
                        raise lib_exc.InvalidCredentials(msg)
            # Populate the network subdict
            for resource in resources:
                if resource == 'network':
                    hash_dict['networks'][temp_hash_key] = resources[resource]
                else:
                    LOG.warning('Unknown resource type %s, ignoring this field'
                                % resource)
        return hash_dict

    def is_multi_user(self):
        # Default credentials is not a valid option with locking Account
        if self.use_default_creds:
            raise lib_exc.InvalidCredentials(
                "Account file %s doesn't exist" % self.test_accounts_file)
        else:
            return len(self.hash_dict['creds']) > 1

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
        # Cast as a list because in some edge cases a set will be passed in
        hashes = list(hashes)
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
        raise lib_exc.InvalidCredentials(msg)

    def _get_match_hash_list(self, roles=None):
        hashes = []
        if roles:
            # Loop over all the creds for each role in the subdict and generate
            # a list of cred lists for each role
            for role in roles:
                temp_hashes = self.hash_dict['roles'].get(role, None)
                if not temp_hashes:
                    raise lib_exc.InvalidCredentials(
                        "No credentials with role: %s specified in the "
                        "accounts ""file" % role)
                hashes.append(temp_hashes)
            # Take the list of lists and do a boolean and between each list to
            # find the creds which fall under all the specified roles
            temp_list = set(hashes[0])
            for hash_list in hashes[1:]:
                temp_list = temp_list & set(hash_list)
            hashes = temp_list
        else:
            hashes = self.hash_dict['creds'].keys()
        # NOTE(mtreinish): admin is a special case because of the increased
        # privilege set which could potentially cause issues on tests where
        # that is not expected. So unless the admin role isn't specified do
        # not allocate admin.
        admin_hashes = self.hash_dict['roles'].get(self.admin_role,
                                                   None)
        if ((not roles or self.admin_role not in roles) and
                admin_hashes):
            useable_hashes = [x for x in hashes if x not in admin_hashes]
        else:
            useable_hashes = hashes
        return useable_hashes

    def _sanitize_creds(self, creds):
        temp_creds = creds.copy()
        temp_creds.pop('password')
        return temp_creds

    def _get_creds(self, roles=None):
        if self.use_default_creds:
            raise lib_exc.InvalidCredentials(
                "Account file %s doesn't exist" % self.test_accounts_file)
        useable_hashes = self._get_match_hash_list(roles)
        free_hash = self._get_free_hash(useable_hashes)
        clean_creds = self._sanitize_creds(
            self.hash_dict['creds'][free_hash])
        LOG.info('%s allocated creds:\n%s' % (self.name, clean_creds))
        return self._wrap_creds_with_network(free_hash)

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
        for _hash in self.hash_dict['creds']:
            # Comparing on the attributes that are expected in the YAML
            init_attributes = creds.get_init_attributes()
            hash_attributes = self.hash_dict['creds'][_hash].copy()
            if ('user_domain_name' in init_attributes and 'user_domain_name'
                    not in hash_attributes):
                # Allow for the case of domain_name populated from config
                domain_name = self.credentials_domain
                hash_attributes['user_domain_name'] = domain_name
            if all([getattr(creds, k) == hash_attributes[k] for
                   k in init_attributes]):
                return _hash
        raise AttributeError('Invalid credentials %s' % creds)

    def remove_credentials(self, creds):
        _hash = self.get_hash(creds)
        clean_creds = self._sanitize_creds(self.hash_dict['creds'][_hash])
        self.remove_hash(_hash)
        LOG.info("%s returned allocated creds:\n%s" % (self.name, clean_creds))

    def get_primary_creds(self):
        if self._creds.get('primary'):
            return self._creds.get('primary')
        net_creds = self._get_creds()
        self._creds['primary'] = net_creds
        return net_creds

    def get_alt_creds(self):
        if self._creds.get('alt'):
            return self._creds.get('alt')
        net_creds = self._get_creds()
        self._creds['alt'] = net_creds
        return net_creds

    def get_creds_by_roles(self, roles, force_new=False):
        roles = list(set(roles))
        exist_creds = self._creds.get(six.text_type(roles).encode(
            'utf-8'), None)
        # The force kwarg is used to allocate an additional set of creds with
        # the same role list. The index used for the previously allocation
        # in the _creds dict will be moved.
        if exist_creds and not force_new:
            return exist_creds
        elif exist_creds and force_new:
            new_index = six.text_type(roles).encode('utf-8') + '-' + \
                six.text_type(len(self._creds)).encode('utf-8')
            self._creds[new_index] = exist_creds
        net_creds = self._get_creds(roles=roles)
        self._creds[six.text_type(roles).encode('utf-8')] = net_creds
        return net_creds

    def clear_creds(self):
        for creds in self._creds.values():
            self.remove_credentials(creds)

    def get_admin_creds(self):
        return self.get_creds_by_roles([self.admin_role])

    def is_role_available(self, role):
        if self.use_default_creds:
            return False
        else:
            if self.hash_dict['roles'].get(role):
                return True
            return False

    def admin_available(self):
        return self.is_role_available(self.admin_role)

    def _wrap_creds_with_network(self, hash):
        creds_dict = self.hash_dict['creds'][hash]
        # Make sure a domain scope if defined for users in case of V3
        # Make sure a tenant is available in case of V2
        creds_dict = self._extend_credentials(creds_dict)
        # This just builds a Credentials object, it does not validate
        # nor fill  with missing fields.
        credential = auth.get_credentials(
            auth_url=None, fill_in=False,
            identity_version=self.identity_version, **creds_dict)
        net_creds = cred_provider.TestResources(credential)
        net_clients = clients.Manager(credentials=credential)
        compute_network_client = net_clients.compute_networks_client
        net_name = self.hash_dict['networks'].get(hash, None)
        try:
            network = fixed_network.get_network_from_name(
                net_name, compute_network_client)
        except exceptions.InvalidTestResource:
            network = {}
        net_creds.set_resources(network=network)
        return net_creds

    def _extend_credentials(self, creds_dict):
        # In case of v3, adds a user_domain_name field to the creds
        # dict if not defined
        if self.identity_version == 'v3':
            user_domain_fields = set(['user_domain_name', 'user_domain_id'])
            if not user_domain_fields.intersection(set(creds_dict.keys())):
                creds_dict['user_domain_name'] = self.credentials_domain
        # NOTE(andreaf) In case of v2, replace project with tenant if project
        # is provided and tenant is not
        if self.identity_version == 'v2':
            if ('project_name' in creds_dict and
                    'tenant_name' in creds_dict and
                    creds_dict['project_name'] != creds_dict['tenant_name']):
                clean_creds = self._sanitize_creds(creds_dict)
                msg = 'Cannot specify project and tenant at the same time %s'
                raise exceptions.InvalidCredentials(msg % clean_creds)
            if ('project_name' in creds_dict and
                    'tenant_name' not in creds_dict):
                creds_dict['tenant_name'] = creds_dict['project_name']
                creds_dict.pop('project_name')
        return creds_dict
