# Copyright 2014 OpenStack Foundation
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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.volume import hosts as schema
from tempest.lib.common import rest_client


class HostsClient(rest_client.RestClient):
    """Client class to send CRUD Volume API requests"""

    def list_hosts(self, **params):
        """Lists all hosts.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-all-hosts-for-a-project
        """
        url = 'os-hosts'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_hosts, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_host(self, host_name):
        """Show host details."""
        url = 'os-hosts/%s' % host_name
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.show_host, resp, body)
        return rest_client.ResponseBody(resp, body)
