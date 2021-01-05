# Copyright 2013 NEC Corporation
# Copyright 2013 IBM Corp.
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

from tempest.lib.api_schema.response.compute.v2_1 import services as schema
from tempest.lib.api_schema.response.compute.v2_11 import services \
    as schemav211
from tempest.lib.api_schema.response.compute.v2_53 import services \
    as schemav253
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class ServicesClient(base_compute_client.BaseComputeClient):

    schema_versions_info = [
        {'min': None, 'max': '2.10', 'schema': schema},
        {'min': '2.11', 'max': '2.52', 'schema': schemav211},
        {'min': '2.53', 'max': None, 'schema': schemav253}]

    def list_services(self, **params):
        """Lists all running Compute services for a tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-compute-services
        """
        url = 'os-services'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        _schema = self.get_schema(self.schema_versions_info)
        self.validate_response(_schema.list_services, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_service(self, service_id, **kwargs):
        """Update a compute service.

        Update a compute service to enable or disable scheduling, including
        recording a reason why a compute service was disabled from scheduling.

        This API is available starting with microversion 2.53.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#update-compute-service
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/%s' % service_id, put_body)
        body = json.loads(body)
        _schema = self.get_schema(self.schema_versions_info)
        self.validate_response(_schema.update_service, resp, body)
        return rest_client.ResponseBody(resp, body)

    def enable_service(self, **kwargs):
        """Enable service on a host.

        ``update_service`` supersedes this API starting with microversion 2.53.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#enable-scheduling-for-a-compute-service
        """
        post_body = json.dumps(kwargs)
        resp, body = self.put('os-services/enable', post_body)
        body = json.loads(body)
        self.validate_response(schema.enable_disable_service, resp, body)
        return rest_client.ResponseBody(resp, body)

    def disable_service(self, **kwargs):
        """Disable service on a host.

        ``update_service`` supersedes this API starting with microversion 2.53.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#disable-scheduling-for-a-compute-service
        """
        post_body = json.dumps(kwargs)
        resp, body = self.put('os-services/disable', post_body)
        body = json.loads(body)
        self.validate_response(schema.enable_disable_service, resp, body)
        return rest_client.ResponseBody(resp, body)

    def disable_log_reason(self, **kwargs):
        """Disables scheduling for a Compute service and logs reason.

        ``update_service`` supersedes this API starting with microversion 2.53.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#disable-scheduling-for-a-compute-service-and-log-disabled-reason
        """
        post_body = json.dumps(kwargs)
        resp, body = self.put('os-services/disable-log-reason', post_body)
        body = json.loads(body)
        self.validate_response(schema.disable_log_reason, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_forced_down(self, **kwargs):
        """Set or unset ``forced_down`` flag for the service.

        ``update_service`` supersedes this API starting with microversion 2.53.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#update-forced-down
        """
        post_body = json.dumps(kwargs)
        resp, body = self.put('os-services/force-down', post_body)
        body = json.loads(body)
        # NOTE: Use schemav211.update_forced_down directly because there is no
        # update_forced_down schema for <2.11.
        self.validate_response(schemav211.update_forced_down, resp, body)
        return rest_client.ResponseBody(resp, body)
