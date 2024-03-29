# Copyright 2012 NTT Data
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

from tempest.lib.api_schema.response.compute.v2_1\
    import quota_classes as schema
from tempest.lib.api_schema.response.compute.v2_50 import quota_classes \
    as schemav250
from tempest.lib.api_schema.response.compute.v2_57 import quota_classes \
    as schemav257
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class QuotaClassesClient(base_compute_client.BaseComputeClient):

    schema_versions_info = [
        {'min': None, 'max': '2.49', 'schema': schema},
        {'min': '2.50', 'max': '2.56', 'schema': schemav250},
        {'min': '2.57', 'max': None, 'schema': schemav257}]

    def show_quota_class_set(self, quota_class_id):
        """List the quota class set for a quota class."""

        url = 'os-quota-class-sets/%s' % quota_class_id
        resp, body = self.get(url)
        body = json.loads(body)
        _schema = self.get_schema(self.schema_versions_info)
        self.validate_response(_schema.get_quota_class_set, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_quota_class_set(self, quota_class_id, **kwargs):
        """Update the quota class's limits for one or more resources.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-or-update-quotas-for-quota-class
        """
        post_body = json.dumps({'quota_class_set': kwargs})

        resp, body = self.put('os-quota-class-sets/%s' % quota_class_id,
                              post_body)

        body = json.loads(body)
        _schema = self.get_schema(self.schema_versions_info)
        self.validate_response(_schema.update_quota_class_set,
                               resp, body)
        return rest_client.ResponseBody(resp, body)
