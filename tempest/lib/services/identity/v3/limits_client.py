# Copyright 2021 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class LimitsClient(rest_client.RestClient):
    api_version = "v3"

    def get_registered_limits(self):
        """Lists all registered limits."""
        resp, body = self.get('registered_limits')
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, json.loads(body))

    def create_limit(self, region_id, service_id, project_id, resource_name,
                     default_limit, description=None, domain_id=None):
        """Creates a limit in keystone."""
        limit = {
            'service_id': service_id,
            'project_id': project_id,
            'resource_name': resource_name,
            'resource_limit': default_limit,
            'region_id': region_id,
            'description': description or '%s limit for %s' % (
                resource_name, project_id),
        }
        if domain_id:
            limit['domain_id'] = domain_id
        post_body = json.dumps({'limits': [limit]})
        resp, body = self.post('limits', post_body)
        self.expected_success(201, resp.status)
        return rest_client.ResponseBody(resp, json.loads(body))

    def update_limit(self, limit_id, resource_limit, description=None):
        """Updates a limit in keystone by id."""

        limit = {'resource_limit': resource_limit}
        if description:
            limit['description'] = description
        patch_body = json.dumps({'limit': limit})
        resp, body = self.patch('limits/%s' % limit_id, patch_body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, json.loads(body))
