# Copyright 2017 AT&T Corporation.
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


class OAUTHConsumerClient(rest_client.RestClient):
    api_version = "v3"

    def create_consumer(self, description=None):
        """Creates a consumer.

        :param str description: Optional field to add notes about the consumer

        For more information, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#create-consumer
        """
        post_body = {"description": description}
        post_body = json.dumps({'consumer': post_body})
        resp, body = self.post('OS-OAUTH1/consumers', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_consumer(self, consumer_id):
        """Deletes a consumer.

        :param str consumer_id: The ID of the consumer that will be deleted

        For more information, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#delete-consumer
        """
        resp, body = self.delete('OS-OAUTH1/consumers/%s' % consumer_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_consumer(self, consumer_id, description=None):
        """Updates a consumer.

        :param str consumer_id: The ID of the consumer that will be updated
        :param str description: Optional field to add notes about the consumer

        For more information, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#update-consumer
        """
        post_body = {"description": description}
        post_body = json.dumps({'consumer': post_body})
        resp, body = self.patch('OS-OAUTH1/consumers/%s' % consumer_id,
                                post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_consumer(self, consumer_id):
        """Show consumer details.

        :param str consumer_id: The ID of the consumer that will be shown

        For more information, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#show-consumer-details
        """
        resp, body = self.get('OS-OAUTH1/consumers/%s' % consumer_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_consumers(self):
        """List all consumers.

        For more information, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#list-consumers
        """
        resp, body = self.get('OS-OAUTH1/consumers')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
