# Copyright 2016 VMware, Inc.  All rights reserved.
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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib.services.network import base


class NetworkVersionsClient(base.BaseNetworkClient):

    def list_versions(self):
        """Do a GET / to fetch available API version information.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-api-versions
        """

        # Note: we do a self.get('/') here because we want to use
        # an unversioned URL, not "v2/$project_id/".
        resp, body = self.get('/')
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_version(self, version):
        """Do a GET /<version> to fetch available resources.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-api-v2-details
        """

        resp, body = self.get(version + '/')
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
