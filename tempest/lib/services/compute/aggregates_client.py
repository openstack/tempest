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

from tempest.lib.api_schema.response.compute.v2_1 import aggregates as schema
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import base_compute_client


class AggregatesClient(base_compute_client.BaseComputeClient):

    def list_aggregates(self):
        """Get aggregate list."""
        resp, body = self.get("os-aggregates")
        body = json.loads(body)
        self.validate_response(schema.list_aggregates, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_aggregate(self, aggregate_id):
        """Get details of the given aggregate."""
        resp, body = self.get("os-aggregates/%s" % aggregate_id)
        body = json.loads(body)
        self.validate_response(schema.get_aggregate, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_aggregate(self, **kwargs):
        """Create a new aggregate.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#createAggregate
        """
        post_body = json.dumps({'aggregate': kwargs})
        resp, body = self.post('os-aggregates', post_body)

        body = json.loads(body)
        self.validate_response(schema.create_aggregate, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_aggregate(self, aggregate_id, **kwargs):
        """Update an aggregate.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#updateAggregate
        """
        put_body = json.dumps({'aggregate': kwargs})
        resp, body = self.put('os-aggregates/%s' % aggregate_id, put_body)

        body = json.loads(body)
        self.validate_response(schema.update_aggregate, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_aggregate(self, aggregate_id):
        """Delete the given aggregate."""
        resp, body = self.delete("os-aggregates/%s" % aggregate_id)
        self.validate_response(schema.delete_aggregate, resp, body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_aggregate(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Return the primary type of resource this client works with."""
        return 'aggregate'

    def add_host(self, aggregate_id, **kwargs):
        """Add a host to the given aggregate.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#addHost
        """
        post_body = json.dumps({'add_host': kwargs})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.aggregate_add_remove_host, resp, body)
        return rest_client.ResponseBody(resp, body)

    def remove_host(self, aggregate_id, **kwargs):
        """Remove a host from the given aggregate.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#removeAggregateHost
        """
        post_body = json.dumps({'remove_host': kwargs})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.aggregate_add_remove_host, resp, body)
        return rest_client.ResponseBody(resp, body)

    def set_metadata(self, aggregate_id, **kwargs):
        """Replace the aggregate's existing metadata with new metadata.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#addAggregateMetadata
        """
        post_body = json.dumps({'set_metadata': kwargs})
        resp, body = self.post('os-aggregates/%s/action' % aggregate_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.aggregate_set_metadata, resp, body)
        return rest_client.ResponseBody(resp, body)
