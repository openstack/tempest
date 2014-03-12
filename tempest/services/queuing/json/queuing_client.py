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

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class QueuingClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(QueuingClientJSON, self).__init__(auth_provider)
        self.service = CONF.queuing.catalog_type
        self.version = '1'
        self.uri_prefix = 'v{0}'.format(self.version)

    def list_queues(self):
        uri = '{0}/queues'.format(self.uri_prefix)
        resp, body = self.get(uri)
        body = json.loads(body)
        return resp, body

    def create_queue(self, queue_name):
        uri = '{0}/queues/{1}'.format(self.uri_prefix, queue_name)
        resp, body = self.put(uri, body=None)
        return resp, body

    def get_queue(self, queue_name):
        uri = '{0}/queues/{1}'.format(self.uri_prefix, queue_name)
        resp, body = self.get(uri)
        body = json.loads(body)
        return resp, body

    def head_queue(self, queue_name):
        uri = '{0}/queues/{1}'.format(self.uri_prefix, queue_name)
        resp, body = self.head(uri)
        body = json.loads(body)
        return resp, body

    def delete_queue(self, queue_name):
        uri = '{0}/queues/{1}'.format(self.uri_prefix, queue_name)
        resp = self.delete(uri)
        return resp
