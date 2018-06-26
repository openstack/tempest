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

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class ServicesClient(rest_client.RestClient):
    """Client class to send CRUD Volume Services API requests"""

    def list_services(self, **params):
        """List all Cinder services.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#list-all-cinder-services
        """
        url = 'os-services'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def enable_service(self, **kwargs):
        """Enable service on a host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#enable-a-cinder-service
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/enable', put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def disable_service(self, **kwargs):
        """Disable service on a host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#disable-a-cinder-service
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/disable', put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def disable_log_reason(self, **kwargs):
        """Disable scheduling for a volume service and log disabled reason.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#log-disabled-cinder-service-information
        """
        put_body = json.dumps(kwargs)
        resp, body = self.put('os-services/disable-log-reason', put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def freeze_host(self, **kwargs):
        """Freeze a Cinder backend host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#freeze-a-cinder-backend-host
        """
        put_body = json.dumps(kwargs)
        resp, _ = self.put('os-services/freeze', put_body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp)

    def thaw_host(self, **kwargs):
        """Thaw a Cinder backend host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#thaw-a-cinder-backend-host
        """
        put_body = json.dumps(kwargs)
        resp, _ = self.put('os-services/thaw', put_body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp)
