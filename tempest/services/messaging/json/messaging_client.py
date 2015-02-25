# Copyright (c) 2014 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import urllib
import uuid

from tempest.api_schema.response.messaging.v1 import queues as queues_schema
from tempest.common import service_client


class MessagingClientJSON(service_client.ServiceClient):

    def __init__(self, auth_provider, service, region,
                 endpoint_type=None, build_interval=None, build_timeout=None,
                 disable_ssl_certificate_validation=None, ca_certs=None,
                 trace_requests=None):
        dscv = disable_ssl_certificate_validation
        super(MessagingClientJSON, self).__init__(
            auth_provider, service, region,
            endpoint_type=endpoint_type,
            build_interval=build_interval,
            build_timeout=build_timeout,
            disable_ssl_certificate_validation=dscv,
            ca_certs=ca_certs,
            trace_requests=trace_requests)

        self.version = '1'
        self.uri_prefix = 'v{0}'.format(self.version)

        client_id = uuid.uuid4().hex
        self.headers = {'Client-ID': client_id}

    def list_queues(self):
        uri = '{0}/queues'.format(self.uri_prefix)
        resp, body = self.get(uri)

        if resp['status'] != '204':
            body = json.loads(body)
            self.validate_response(queues_schema.list_queues, resp, body)
        return resp, body

    def create_queue(self, queue_name):
        uri = '{0}/queues/{1}'.format(self.uri_prefix, queue_name)
        resp, body = self.put(uri, body=None)
        self.expected_success(201, resp.status)
        return resp, body

    def get_queue(self, queue_name):
        uri = '{0}/queues/{1}'.format(self.uri_prefix, queue_name)
        resp, body = self.get(uri)
        self.expected_success(204, resp.status)
        return resp, body

    def head_queue(self, queue_name):
        uri = '{0}/queues/{1}'.format(self.uri_prefix, queue_name)
        resp, body = self.head(uri)
        self.expected_success(204, resp.status)
        return resp, body

    def delete_queue(self, queue_name):
        uri = '{0}/queues/{1}'.format(self.uri_prefix, queue_name)
        resp, body = self.delete(uri)
        self.expected_success(204, resp.status)
        return resp, body

    def get_queue_stats(self, queue_name):
        uri = '{0}/queues/{1}/stats'.format(self.uri_prefix, queue_name)
        resp, body = self.get(uri)
        body = json.loads(body)
        self.validate_response(queues_schema.queue_stats, resp, body)
        return resp, body

    def get_queue_metadata(self, queue_name):
        uri = '{0}/queues/{1}/metadata'.format(self.uri_prefix, queue_name)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return resp, body

    def set_queue_metadata(self, queue_name, rbody):
        uri = '{0}/queues/{1}/metadata'.format(self.uri_prefix, queue_name)
        resp, body = self.put(uri, body=json.dumps(rbody))
        self.expected_success(204, resp.status)
        return resp, body

    def post_messages(self, queue_name, rbody):
        uri = '{0}/queues/{1}/messages'.format(self.uri_prefix, queue_name)
        resp, body = self.post(uri, body=json.dumps(rbody),
                               extra_headers=True,
                               headers=self.headers)

        body = json.loads(body)
        self.validate_response(queues_schema.post_messages, resp, body)
        return resp, body

    def list_messages(self, queue_name):
        uri = '{0}/queues/{1}/messages?echo=True'.format(self.uri_prefix,
                                                         queue_name)
        resp, body = self.get(uri, extra_headers=True, headers=self.headers)

        if resp['status'] != '204':
            body = json.loads(body)
            self.validate_response(queues_schema.list_messages, resp, body)

        return resp, body

    def get_single_message(self, message_uri):
        resp, body = self.get(message_uri, extra_headers=True,
                              headers=self.headers)
        if resp['status'] != '204':
            body = json.loads(body)
            self.validate_response(queues_schema.get_single_message, resp,
                                   body)
        return resp, body

    def get_multiple_messages(self, message_uri):
        resp, body = self.get(message_uri, extra_headers=True,
                              headers=self.headers)

        if resp['status'] != '204':
            body = json.loads(body)
            self.validate_response(queues_schema.get_multiple_messages,
                                   resp,
                                   body)

        return resp, body

    def delete_messages(self, message_uri):
        resp, body = self.delete(message_uri)
        self.expected_success(204, resp.status)
        return resp, body

    def post_claims(self, queue_name, rbody, url_params=False):
        uri = '{0}/queues/{1}/claims'.format(self.uri_prefix, queue_name)
        if url_params:
            uri += '?%s' % urllib.urlencode(url_params)

        resp, body = self.post(uri, body=json.dumps(rbody),
                               extra_headers=True,
                               headers=self.headers)

        body = json.loads(body)
        self.validate_response(queues_schema.claim_messages, resp, body)
        return resp, body

    def query_claim(self, claim_uri):
        resp, body = self.get(claim_uri)

        if resp['status'] != '204':
            body = json.loads(body)
            self.validate_response(queues_schema.query_claim, resp, body)
        return resp, body

    def update_claim(self, claim_uri, rbody):
        resp, body = self.patch(claim_uri, body=json.dumps(rbody))
        self.expected_success(204, resp.status)
        return resp, body

    def release_claim(self, claim_uri):
        resp, body = self.delete(claim_uri)
        self.expected_success(204, resp.status)
        return resp, body
