# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

from tempest import auth
from tempest import config
from tempest import exceptions

CONF = config.CONF


class Manager(object):

    """
    Base manager class

    Manager objects are responsible for providing a configuration object
    and a client object for a test case to use in performing actions.
    """

    def __init__(self, credentials=None):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name[/domain_name] is used.

        :param credentials: Override of the credentials
        """
        self.auth_version = CONF.identity.auth_version
        if credentials is None:
            self.credentials = auth.get_default_credentials('user')
        else:
            self.credentials = credentials
        # Check if passed or default credentials are valid
        if not self.credentials.is_valid():
            raise exceptions.InvalidCredentials()
        # Creates an auth provider for the credentials
        self.auth_provider = self.get_auth_provider(self.credentials)
        # FIXME(andreaf) unused
        self.client_attr_names = []

    @classmethod
    def get_auth_provider_class(cls, auth_version):
        if auth_version == 'v2':
            return auth.KeystoneV2AuthProvider
        else:
            return auth.KeystoneV3AuthProvider

    def get_auth_provider(self, credentials):
        if credentials is None:
            raise exceptions.InvalidCredentials(
                'Credentials must be specified')
        auth_provider_class = self.get_auth_provider_class(self.auth_version)
        return auth_provider_class(
            client_type=getattr(self, 'client_type', None),
            interface=getattr(self, 'interface', None),
            credentials=credentials)
