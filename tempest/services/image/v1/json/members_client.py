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


class MembersClient(rest_client.RestClient):
    api_version = "v1"

    def list_image_members(self, image_id):
        """List all members of an image."""
        url = 'images/%s/members' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_shared_images(self, tenant_id):
        """List image memberships for the given tenant.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v1.html#listSharedImages-v1
        """

        url = 'shared-images/%s' % tenant_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def add_member(self, member_id, image_id, **kwargs):
        """Add a member to an image.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v1.html#addMember-v1
        """
        url = 'images/%s/members/%s' % (image_id, member_id)
        body = json.dumps({'member': kwargs})
        resp, __ = self.put(url, body)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def delete_member(self, member_id, image_id):
        """Removes a membership from the image.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v1.html#removeMember-v1
        """
        url = 'images/%s/members/%s' % (image_id, member_id)
        resp, __ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
