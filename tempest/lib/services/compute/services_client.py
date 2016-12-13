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

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.api_schema.response.compute.v2_1 import services as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class ServicesClient(base_compute_client.BaseComputeClient):

    def list_services(self, **params):
        """Lists all running Compute services for a tenant.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#listServices
        """
        url = 'os-services'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_services, resp, body)
        return rest_client.ResponseBody(resp, body)

    def enable_service(self, **kwargs):
        """Enable service on a host.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#enableScheduling
        """
        post_body = json.dumps(kwargs)
        resp, body = self.put('os-services/enable', post_body)
        body = json.loads(body)
        self.validate_response(schema.enable_disable_service, resp, body)
        return rest_client.ResponseBody(resp, body)

    def disable_service(self, **kwargs):
        """Disable service on a host.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#disableScheduling
        """
        post_body = json.dumps(kwargs)
        resp, body = self.put('os-services/disable', post_body)
        body = json.loads(body)
        self.validate_response(schema.enable_disable_service, resp, body)
        return rest_client.ResponseBody(resp, body)
