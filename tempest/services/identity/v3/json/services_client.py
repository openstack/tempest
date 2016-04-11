# Copyright 2013 OpenStack Foundation
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

"""
http://developer.openstack.org/api-ref-identity-v3.html#service-catalog-v3
"""

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class ServicesClient(rest_client.RestClient):
    api_version = "v3"

    def update_service(self, service_id, **kwargs):
        """Updates a service.

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v3.html#updateService
        """
        patch_body = json.dumps({'service': kwargs})
        resp, body = self.patch('services/%s' % service_id, patch_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_service(self, service_id):
        """Get Service."""
        url = 'services/%s' % service_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_service(self, **kwargs):
        """Creates a service.

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v3.html#createService
        """
        body = json.dumps({'service': kwargs})
        resp, body = self.post("services", body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_service(self, serv_id):
        url = "services/" + serv_id
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_services(self):
        resp, body = self.get('services')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
