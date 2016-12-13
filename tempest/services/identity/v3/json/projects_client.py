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

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class ProjectsClient(rest_client.RestClient):
    api_version = "v3"

    def create_project(self, name, **kwargs):
        """Create a Project.

        Available params: see http://developer.openstack.org/
                          api-ref-identity-v3.html#createProject

        """
        # Include the project name to the kwargs parameters
        kwargs['name'] = name
        post_body = json.dumps({'project': kwargs})
        resp, body = self.post('projects', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_projects(self, params=None):
        url = "projects"
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_project(self, project_id, **kwargs):
        """Update a Project.

        Available params: see http://developer.openstack.org/
                          api-ref-identity-v3.html#updateProject

        """
        post_body = json.dumps({'project': kwargs})
        resp, body = self.patch('projects/%s' % project_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_project(self, project_id):
        """GET a Project."""
        resp, body = self.get("projects/%s" % project_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_project(self, project_id):
        """Delete a project."""
        resp, body = self.delete('projects/%s' % str(project_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
