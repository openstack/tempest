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

import json
import urllib

from tempest.api_schema.response.compute import services as schema
from tempest.common import service_client


class ServicesClientJSON(service_client.ServiceClient):

    def list_services(self, params=None):
        url = 'os-services'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_services, resp, body)
        return service_client.ResponseBodyList(resp, body['services'])

    def enable_service(self, host_name, binary):
        """
        Enable service on a host
        host_name: Name of host
        binary: Service binary
        """
        post_body = json.dumps({'binary': binary, 'host': host_name})
        resp, body = self.put('os-services/enable', post_body)
        body = json.loads(body)
        self.validate_response(schema.enable_service, resp, body)
        return service_client.ResponseBody(resp, body['service'])

    def disable_service(self, host_name, binary):
        """
        Disable service on a host
        host_name: Name of host
        binary: Service binary
        """
        post_body = json.dumps({'binary': binary, 'host': host_name})
        resp, body = self.put('os-services/disable', post_body)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body['service'])
