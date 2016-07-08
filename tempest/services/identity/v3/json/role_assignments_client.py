# Copyright 2016 Red Hat, Inc.
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


class RoleAssignmentsClient(rest_client.RestClient):
    api_version = "v3"

    def list_user_project_effective_assignments(
            self, project_id, user_id):
        """List the effective role assignments for a user in a project."""
        resp, body = self.get(
            "role_assignments?scope.project.id=%s&user.id=%s&effective" %
            (project_id, user_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
