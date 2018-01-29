# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class QuotaClassesClient(rest_client.RestClient):
    """Volume quota class V2 client."""

    api_version = "v2"

    def show_quota_class_set(self, quota_class_id):
        """List quotas for a quota class.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v2/index.html#show-quota-classes
        """
        url = 'os-quota-class-sets/%s' % quota_class_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_quota_class_set(self, quota_class_id, **kwargs):
        """Update quotas for a quota class.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v2/index.html#update-quota-classes
        """
        url = 'os-quota-class-sets/%s' % quota_class_id
        put_body = json.dumps({'quota_class_set': kwargs})
        resp, body = self.put(url, put_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
