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

    def __init__(self, username=None, password=None, tenant_name=None):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name[/domain_name] is used.

        :param credentials: Override of the credentials
        """
        self.auth_version = CONF.identity.auth_version
        # FIXME(andreaf) Change Manager __init__ to accept a credentials dict
        if username is None or password is None:
            # Tenant None is a valid use case
            self.credentials = self.get_default_credentials()
        else:
            self.credentials = dict(username=username, password=password,
                                    tenant_name=tenant_name)
        if self.auth_version == 'v3':
            self.credentials['domain_name'] = 'Default'
        # Creates an auth provider for the credentials
        self.auth_provider = self.get_auth_provider(self.credentials)
        # FIXME(andreaf) unused
        self.client_attr_names = []

    # we do this everywhere, have it be part of the super class
    def _validate_credentials(self, username, password, tenant_name):
        if None in (username, password, tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(u)s, password: %(p)s, "
                   "tenant_name: %(t)s" %
                   {'u': username, 'p': password, 't': tenant_name})
            raise exceptions.InvalidConfiguration(msg)

    @classmethod
    def get_auth_provider_class(cls, auth_version):
        if auth_version == 'v2':
            return auth.KeystoneV2AuthProvider
        else:
            return auth.KeystoneV3AuthProvider

    def get_default_credentials(self):
        return dict(
            username=CONF.identity.username,
            password=CONF.identity.password,
            tenant_name=CONF.identity.tenant_name
        )

    def get_auth_provider(self, credentials=None):
        auth_params = dict(client_type=getattr(self, 'client_type', None),
                           interface=getattr(self, 'interface', None))
        auth_provider_class = self.get_auth_provider_class(self.auth_version)
        # If invalid / incomplete credentials are provided, use default ones
        if credentials is None or \
                not auth_provider_class.check_credentials(credentials):
            credentials = self.credentials
        auth_params['credentials'] = credentials
        return auth_provider_class(**auth_params)
