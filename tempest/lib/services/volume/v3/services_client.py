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

from tempest.lib.api_schema.response.volume import services as schema
from tempest.lib.api_schema.response.volume.v3_7 import services as schemav37
from tempest.lib.common import rest_client
from tempest.lib.services.volume import base_client


class ServicesClient(base_client.BaseClient):
    """Client class to send CRUD Volume Services API requests"""

    schema_versions_info = [
        {'min': None, 'max': '3.6', 'schema': schema},
        {'min': '3.7', 'max': None, 'schema': schemav37}]

    def list_services(self, **params):
        """List all Cinder services.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#list-all-cinder-services
        """
        url = 'os-services'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.list_services, resp, body)
        return rest_client.ResponseBody(resp, body)

    def enable_service(self, **kwargs):
        """Enable service on a host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#enable-a-cinder-service
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/enable', put_body)
        body = json.loads(body)
        self.validate_response(schema.enable_service, resp, body)
        return rest_client.ResponseBody(resp, body)

    def disable_service(self, **kwargs):
        """Disable service on a host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#disable-a-cinder-service
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/disable', put_body)
        body = json.loads(body)
        self.validate_response(schema.disable_service, resp, body)
        return rest_client.ResponseBody(resp, body)

    def disable_log_reason(self, **kwargs):
        """Disable scheduling for a volume service and log disabled reason.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#log-disabled-cinder-service-information
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/disable-log-reason', put_body)
        body = json.loads(body)
        self.validate_response(schema.disable_log_reason, resp, body)
        return rest_client.ResponseBody(resp, body)

    def freeze_host(self, **kwargs):
        """Freeze a Cinder backend host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#freeze-a-cinder-backend-host
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/freeze', put_body)
        self.validate_response(schema.freeze_host, resp, body)
        return rest_client.ResponseBody(resp)

    def thaw_host(self, **kwargs):
        """Thaw a Cinder backend host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#thaw-a-cinder-backend-host
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/thaw', put_body)
        self.validate_response(schema.thaw_host, resp, body)
        return rest_client.ResponseBody(resp)
