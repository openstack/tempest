# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation.
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

import json

from tempest.common.rest_client import RestClient
from tempest import exceptions


class AggregatesV3ClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(AggregatesV3ClientJSON, self).__init__(config, username,
                                                     password, auth_url,
                                                     tenant_name)
        self.service = self.config.compute.catalog_v3_type

    def list_aggregates(self):
        """Get aggregate list."""
        resp, body = self.get("os-aggregates")
        body = json.loads(body)
        return resp, body['aggregates']

    def get_aggregate(self, aggregate_id):
        """Get details of the given aggregate."""
        resp, body = self.get("os-aggregates/%s" % str(aggregate_id))
        body = json.loads(body)
        return resp, body['aggregate']

    def create_aggregate(self, name, availability_zone=None):
        """Creates a new aggregate."""
        post_body = {
            'name': name,
            'availability_zone': availability_zone,
        }
        post_body = json.dumps({'aggregate': post_body})
        resp, body = self.post('os-aggregates', post_body, self.headers)

        body = json.loads(body)
        return resp, body['aggregate']

    def update_aggregate(self, aggregate_id, name, availability_zone=None):
        """Update a aggregate."""
        put_body = {
            'name': name,
            'availability_zone': availability_zone
        }
        put_body = json.dumps({'aggregate': put_body})
        resp, body = self.put('os-aggregates/%s' % str(aggregate_id),
                              put_body, self.headers)

        body = json.loads(body)
        return resp, body['aggregate']

    def delete_aggregate(self, aggregate_id):
        """Deletes the given aggregate."""
        return self.delete("os-aggregates/%s" % str(aggregate_id))

    def is_resource_deleted(self, id):
        try:
            self.get_aggregate(id)
        except exceptions.NotFound:
            return True
        return False

    def add_host(self, aggregate_id, host):
        """Adds a host to the given aggregate."""
        post_body = {
            'host': host,
        }
        post_body = json.dumps({'add_host': post_body})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body, self.headers)
        body = json.loads(body)
        return resp, body['aggregate']

    def remove_host(self, aggregate_id, host):
        """Removes a host from the given aggregate."""
        post_body = {
            'host': host,
        }
        post_body = json.dumps({'remove_host': post_body})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body, self.headers)
        body = json.loads(body)
        return resp, body['aggregate']

    def set_metadata(self, aggregate_id, meta):
        """Replaces the aggregate's existing metadata with new metadata."""
        post_body = {
            'metadata': meta,
        }
        post_body = json.dumps({'set_metadata': post_body})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body, self.headers)
        body = json.loads(body)
        return resp, body['aggregate']
