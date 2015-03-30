# Copyright 2013 IBM Corp
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

from tempest.api_schema.response.compute.v2_1 import certificates as schema
from tempest.common import service_client


class CertificatesClientJSON(service_client.ServiceClient):

    def get_certificate(self, id):
        url = "os-certificates/%s" % (id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.get_certificate, resp, body)
        return service_client.ResponseBody(resp, body['certificate'])

    def create_certificate(self):
        """create certificates."""
        url = "os-certificates"
        resp, body = self.post(url, None)
        body = json.loads(body)
        self.validate_response(schema.create_certificate, resp, body)
        return service_client.ResponseBody(resp, body['certificate'])
