# Copyright 2014 Hewlett-Packard Development Company, L.P.
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


class FakeCredentials(auth.Credentials):

    def is_valid(self):
        return True


class FakeKeystoneV2Credentials(auth.KeystoneV2Credentials):

    def __init__(self):
        creds = dict(
            username='fake_username',
            password='fake_password',
            tenant_name='fake_tenant_name'
        )
        super(FakeKeystoneV2Credentials, self).__init__(**creds)


class FakeKeystoneV3Credentials(auth.KeystoneV3Credentials):
    """
    Fake credentials suitable for the Keystone Identity V3 API
    """

    def __init__(self):
        creds = dict(
            username='fake_username',
            password='fake_password',
            user_domain_name='fake_domain_name',
            project_name='fake_tenant_name',
            project_domain_name='fake_domain_name'
        )
        super(FakeKeystoneV3Credentials, self).__init__(**creds)


class FakeKeystoneV3DomainCredentials(auth.KeystoneV3Credentials):
    """
    Fake credentials suitable for the Keystone Identity V3 API, with no scope
    """

    def __init__(self):
        creds = dict(
            username='fake_username',
            password='fake_password',
            user_domain_name='fake_domain_name'
        )
        super(FakeKeystoneV3DomainCredentials, self).__init__(**creds)
