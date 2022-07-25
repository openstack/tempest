# Copyright 2022 Red Hat, Inc.
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


class ImageCacheClient(rest_client.RestClient):
    api_version = "v2"

    def list_cache(self):
        """Lists all images in cache or queue. (Since Image API v2.14)

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/?expanded=query-cache-status-detail#cache-manage
        """
        url = 'cache'
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def cache_queue(self, image_id):
        """Queues image for caching. (Since Image API v2.14)

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/?expanded=queue-image-detail#queue-image
        """
        url = 'cache/%s' % image_id
        resp, body = self.put(url, body=None)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body=body)

    def cache_delete(self, image_id):
        """Deletes a image from cache. (Since Image API v2.14)

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/?expanded=delete-image-from-cache-detail#delete-image-from-cache
        """
        url = 'cache/%s' % image_id
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def cache_clear(self, target=None):
        """Clears the cache and its queue. (Since Image API v2.14)

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/?expanded=clear-images-from-cache-detail#delete-image-from-cache
        """
        url = 'cache'
        headers = {}
        if target:
            headers['x-image-cache-clear-target'] = target
        resp, _ = self.delete(url, headers=headers)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
