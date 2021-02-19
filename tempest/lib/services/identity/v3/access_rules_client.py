# Copyright 2019 SUSE LLC
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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class AccessRulesClient(rest_client.RestClient):
    api_version = "v3"

    def show_access_rule(self, user_id, access_rule_id):
        """Gets details of an access rule.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-access-rule-details
        """
        resp, body = self.get('users/%s/access_rules/%s' %
                              (user_id, access_rule_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_access_rules(self, user_id, **params):
        """Lists out all of a user's access rules.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#list-access-rules
        """
        url = 'users/%s/access_rules' % user_id
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_access_rule(self, user_id, access_rule_id):
        """Deletes an access rule.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#delete-access-rule
        """
        resp, body = self.delete('users/%s/access_rules/%s' %
                                 (user_id, access_rule_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
