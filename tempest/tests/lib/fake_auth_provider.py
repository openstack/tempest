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


class FakeAuthProvider(object):

    def __init__(self, creds_dict=None, fake_base_url=None):
        creds_dict = creds_dict or {}
        self.credentials = FakeCredentials(creds_dict)
        self.fake_base_url = fake_base_url

    def auth_request(self, method, url, headers=None, body=None, filters=None):
        return url, headers, body

    def base_url(self, filters, auth_data=None):
        return self.fake_base_url or "https://example.com"

    def get_token(self):
        return "faketoken"


class FakeCredentials(object):

    def __init__(self, creds_dict):
        for key in creds_dict:
            setattr(self, key, creds_dict[key])
