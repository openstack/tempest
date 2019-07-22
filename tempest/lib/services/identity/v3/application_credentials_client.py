# Copyright 2018 SUSE Linux GmbH
#
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

"""
https://docs.openstack.org/api-ref/identity/v3/index.html#application-credentials
"""

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class ApplicationCredentialsClient(rest_client.RestClient):
    api_version = "v3"

    def create_application_credential(self, user_id, **kwargs):
        """Creates an application credential.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#create-application-credential
        """
        post_body = json.dumps({'application_credential': kwargs})
        resp, body = self.post('users/%s/application_credentials' % user_id,
                               post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_application_credential(self, user_id, application_credential_id):
        """Gets details of an application credential.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-application-credential-details
        """
        resp, body = self.get('users/%s/application_credentials/%s' %
                              (user_id, application_credential_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_application_credentials(self, user_id, **params):
        """Lists out all of a user's application credentials.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#list-application-credentials
        """
        url = 'users/%s/application_credentials' % user_id
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_application_credential(self, user_id,
                                      application_credential_id):
        """Deletes an application credential.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#delete-application-credential
        """
        resp, body = self.delete('users/%s/application_credentials/%s' %
                                 (user_id, application_credential_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
