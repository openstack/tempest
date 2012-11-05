# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import json

from tempest.common.rest_client import RestClient


class AccountClient(RestClient):
    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(AccountClient, self).__init__(config, username, password,
                                            auth_url, tenant_name)
        self.service = self.config.object_storage.catalog_type
        self.format = 'json'

    def list_account_metadata(self):
        """
        HEAD on the storage URL
        Returns all account metadata headers
        """

        headers = {"X-Storage-Token": self.token}
        resp, body = self.head('', headers=headers)
        return resp, body

    def create_account_metadata(self, metadata,
                                metadata_prefix='X-Account-Meta-'):
        """Creates an account metadata entry"""
        headers = {}
        for key in metadata:
            headers[metadata_prefix + key] = metadata[key]

        resp, body = self.post('', headers=headers, body=None)
        return resp, body

    def delete_account_metadata(self, metadata,
                                metadata_prefix='X-Remove-Account-Meta-'):
        """
        Deletes an account metadata entry.
        """

        headers = {"X-Storage-Token": self.token}
        for item in metadata:
            headers[metadata_prefix + item] = 'x'
        resp, body = self.post('', headers=headers, body=None)
        return resp, body

    def list_account_containers(self, params=None):
        """
        GET on the (base) storage URL
        Given the X-Storage-URL and a valid X-Auth-Token, returns
        a list of all containers for the account.

        Optional Arguments:
        limit=[integer value N]
            Limits the number of results to at most N values
            DEFAULT:  10,000

        marker=[string value X]
            Given string value X, return object names greater in value
            than the specified marker.
            DEFAULT: No Marker

        format=[string value, either 'json' or 'xml']
            Specify either json or xml to return the respective serialized
            response.
            DEFAULT:  Python-List returned in response body
        """

        param_list = ['format=%s&' % self.format]
        if params is not None:
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))
        url = '?' + ''.join(param_list)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body
