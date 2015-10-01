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

from oslo_serialization import jsonutils as json
from tempest_lib import exceptions as lib_exc

from tempest.api_schema.response.compute.v2_1 import aggregates as schema
from tempest.common import service_client


class AggregatesClient(service_client.ServiceClient):

    def list_aggregates(self):
        """Get aggregate list."""
        resp, body = self.get("os-aggregates")
        body = json.loads(body)
        self.validate_response(schema.list_aggregates, resp, body)
        return service_client.ResponseBody(resp, body)

    def show_aggregate(self, aggregate_id):
        """Get details of the given aggregate."""
        resp, body = self.get("os-aggregates/%s" % aggregate_id)
        body = json.loads(body)
        self.validate_response(schema.get_aggregate, resp, body)
        return service_client.ResponseBody(resp, body)

    def create_aggregate(self, **kwargs):
        """Creates a new aggregate."""
        post_body = json.dumps({'aggregate': kwargs})
        resp, body = self.post('os-aggregates', post_body)

        body = json.loads(body)
        self.validate_response(schema.create_aggregate, resp, body)
        return service_client.ResponseBody(resp, body)

    def update_aggregate(self, aggregate_id, **kwargs):
        """Update a aggregate."""
        put_body = json.dumps({'aggregate': kwargs})
        resp, body = self.put('os-aggregates/%s' % aggregate_id, put_body)

        body = json.loads(body)
        self.validate_response(schema.update_aggregate, resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_aggregate(self, aggregate_id):
        """Deletes the given aggregate."""
        resp, body = self.delete("os-aggregates/%s" % aggregate_id)
        self.validate_response(schema.delete_aggregate, resp, body)
        return service_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_aggregate(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'aggregate'

    def add_host(self, aggregate_id, **kwargs):
        """Adds a host to the given aggregate."""
        post_body = json.dumps({'add_host': kwargs})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.aggregate_add_remove_host, resp, body)
        return service_client.ResponseBody(resp, body)

    def remove_host(self, aggregate_id, **kwargs):
        """Removes a host from the given aggregate."""
        post_body = json.dumps({'remove_host': kwargs})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.aggregate_add_remove_host, resp, body)
        return service_client.ResponseBody(resp, body)

    def set_metadata(self, aggregate_id, **kwargs):
        """Replaces the aggregate's existing metadata with new metadata."""
        post_body = json.dumps({'set_metadata': kwargs})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.aggregate_set_metadata, resp, body)
        return service_client.ResponseBody(resp, body)
