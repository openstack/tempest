# Copyright 2012 OpenStack Foundation
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
from tempest.services.volume.base.admin import base_types_client


class TypesClient(base_types_client.BaseTypesClient):
    """Client class to send CRUD Volume V2 API requests"""
    api_version = "v2"

    def add_type_access(self, volume_type_id, **kwargs):
        """Adds volume type access for the given project.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html
                              #createVolumeTypeAccessExt
        """
        post_body = json.dumps({'addProjectAccess': kwargs})
        url = 'types/%s/action' % volume_type_id
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def remove_type_access(self, volume_type_id, **kwargs):
        """Removes volume type access for the given project.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html
                              #removeVolumeTypeAccessExt
        """
        post_body = json.dumps({'removeProjectAccess': kwargs})
        url = 'types/%s/action' % volume_type_id
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_type_access(self, volume_type_id):
        """Print access information about the given volume type.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html#
                              listVolumeTypeAccessExt
        """
        url = 'types/%s/os-volume-type-access' % volume_type_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
