# Copyright (c) 2014 Deutsche Telekom AG
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

import abc

import six

from tempest import exceptions
from tempest.lib import auth


@six.add_metaclass(abc.ABCMeta)
class CredentialProvider(object):
    def __init__(self, identity_version, name=None, network_resources=None,
                 credentials_domain=None, admin_role=None):
        """A CredentialProvider supplies credentials to test classes.

        :param identity_version: Identity version of the credentials provided
        :param name: Name of the calling test. Included in provisioned
                     credentials when credentials are provisioned on the fly
        :param network_resources: Network resources required for the
                                  credentials
        :param credentials_domain: Domain credentials belong to
        :param admin_role: Name of the role of the admin account
        """
        self.identity_version = identity_version
        self.name = name or "test_creds"
        self.network_resources = network_resources
        self.credentials_domain = credentials_domain or 'Default'
        self.admin_role = admin_role
        if not auth.is_identity_version_supported(self.identity_version):
            raise exceptions.InvalidIdentityVersion(
                identity_version=self.identity_version)

    @abc.abstractmethod
    def get_primary_creds(self):
        return

    @abc.abstractmethod
    def get_admin_creds(self):
        return

    @abc.abstractmethod
    def get_alt_creds(self):
        return

    @abc.abstractmethod
    def clear_creds(self):
        return

    @abc.abstractmethod
    def is_multi_user(self):
        return

    @abc.abstractmethod
    def is_multi_tenant(self):
        return

    @abc.abstractmethod
    def get_creds_by_roles(self, roles, force_new=False):
        return

    @abc.abstractmethod
    def is_role_available(self, role):
        return


class TestResources(object):
    """Readonly Credentials, with network resources added."""

    def __init__(self, credentials):
        self._credentials = credentials
        self.network = None
        self.subnet = None
        self.router = None

    def __getattr__(self, item):
        return getattr(self._credentials, item)

    def set_resources(self, **kwargs):
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

    @property
    def credentials(self):
        return self._credentials
