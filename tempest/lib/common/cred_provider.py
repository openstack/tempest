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
from oslo_log import log as logging

from tempest.lib import auth
from tempest.lib import exceptions

LOG = logging.getLogger(__name__)


class CredentialProvider(object, metaclass=abc.ABCMeta):
    def __init__(self, identity_version, name=None,
                 network_resources=None, credentials_domain=None,
                 admin_role=None, identity_uri=None):
        """A CredentialProvider supplies credentials to test classes.

        :param identity_version: Identity version of the credentials provided
        :param name: Name of the calling test. Included in provisioned
                     credentials when credentials are provisioned on the fly
        :param network_resources: Network resources required for the
                                  credentials
        :param credentials_domain: Domain credentials belong to
        :param admin_role: Name of the role of the admin account
        :param identity_uri: Identity URI of the target cloud. This *must* be
                             specified for anything to work.
        """
        self.identity_version = identity_version
        self.identity_uri = identity_uri
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
    def get_system_admin_creds(self):
        return

    @abc.abstractmethod
    def get_system_member_creds(self):
        return

    @abc.abstractmethod
    def get_system_reader_creds(self):
        return

    @abc.abstractmethod
    def get_domain_admin_creds(self):
        return

    @abc.abstractmethod
    def get_domain_member_creds(self):
        return

    @abc.abstractmethod
    def get_domain_reader_creds(self):
        return

    @abc.abstractmethod
    def get_project_admin_creds(self):
        return

    @abc.abstractmethod
    def get_project_alt_admin_creds(self):
        return

    @abc.abstractmethod
    def get_project_member_creds(self):
        return

    @abc.abstractmethod
    def get_project_alt_member_creds(self):
        return

    @abc.abstractmethod
    def get_project_reader_creds(self):
        return

    @abc.abstractmethod
    def get_project_alt_reader_creds(self):
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
    def get_creds_by_roles(self, roles, force_new=False, scope=None):
        return

    @abc.abstractmethod
    def is_role_available(self, role):
        return

    def cleanup_default_secgroup(self, security_group_client, tenant):
        resp_body = security_group_client.list_security_groups(
            tenant_id=tenant,
            name="default")
        secgroups_to_delete = resp_body['security_groups']
        for secgroup in secgroups_to_delete:
            try:
                security_group_client.delete_security_group(secgroup['id'])
            except exceptions.NotFound:
                LOG.warning('Security group %s, id %s not found for clean-up',
                            secgroup['name'], secgroup['id'])


class TestResources(object):
    """Readonly Credentials, with network resources added."""

    def __init__(self, credentials):
        self._credentials = credentials
        self.network = None
        self.subnet = None
        self.router = None

    def __getattr__(self, item):
        return getattr(self._credentials, item)

    def __str__(self):
        _format = "Credentials: %s, Network: %s, Subnet: %s, Router: %s"
        return _format % (self._credentials, self.network, self.subnet,
                          self.router)

    def set_resources(self, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

    @property
    def credentials(self):
        return self._credentials
