# Copyright 2018 AT&T Corporation.
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

from tempest.lib.common import rest_client


class ProjectTagsClient(rest_client.RestClient):
    api_version = "v3"

    def update_project_tag(self, project_id, tag):
        """Updates the specified tag and adds it to the project's list of tags.

        """
        url = 'projects/%s/tags/%s' % (project_id, tag)
        resp, body = self.put(url, '{}')
        # NOTE(felipemonteiro): This API endpoint returns 201 AND an empty
        # response body, which is consistent with the spec:
        # https://specs.openstack.org/openstack/api-wg/guidelines/tags.html#addressing-individual-tags
        self.expected_success(201, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_project_tags(self, project_id):
        """List tags for a project."""
        url = "projects/%s/tags" % project_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_all_project_tags(self, project_id, tags, **kwargs):
        """Updates all the tags for a project.

        Any existing tags not specified will be deleted.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#modify-tag-list-for-a-project
        """
        body = {'tags': tags}
        if kwargs:
            body.update(kwargs)
        put_body = json.dumps(body)
        resp, body = self.put('projects/%s/tags' % project_id, put_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def check_project_tag_existence(self, project_id, tag):
        """Check if a project contains a tag."""
        url = 'projects/%s/tags/%s' % (project_id, tag)
        resp, body = self.get(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_project_tag(self, project_id, tag):
        """Delete a project tag."""
        url = 'projects/%s/tags/%s' % (project_id, tag)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_all_project_tags(self, project_id):
        """Delete all tags from a project."""
        resp, body = self.delete('projects/%s/tags' % project_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
