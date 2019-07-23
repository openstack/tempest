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


class ImageMembersClient(rest_client.RestClient):
    api_version = "v2"

    def list_image_members(self, image_id):
        """List image members.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#list-image-members
        """
        url = 'images/%s/members' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_image_member(self, image_id, **kwargs):
        """Create an image member.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#create-image-member
        """
        url = 'images/%s/members' % image_id
        data = json.dumps(kwargs)
        resp, body = self.post(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_image_member(self, image_id, member_id, **kwargs):
        """Update an image member.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#update-image-member
        """
        url = 'images/%s/members/%s' % (image_id, member_id)
        data = json.dumps(kwargs)
        resp, body = self.put(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_image_member(self, image_id, member_id):
        """Show an image member.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#show-image-member-details
        """
        url = 'images/%s/members/%s' % (image_id, member_id)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, json.loads(body))

    def delete_image_member(self, image_id, member_id):
        """Delete an image member.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#delete-image-member
        """
        url = 'images/%s/members/%s' % (image_id, member_id)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
