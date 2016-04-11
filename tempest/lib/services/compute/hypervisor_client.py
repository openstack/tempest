# Copyright 2013 IBM Corporation.
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

from tempest.lib.api_schema.response.compute.v2_1 import hypervisors as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class HypervisorClient(base_compute_client.BaseComputeClient):

    def list_hypervisors(self, detail=False):
        """List hypervisors information."""
        url = 'os-hypervisors'
        _schema = schema.list_search_hypervisors
        if detail:
            url += '/detail'
            _schema = schema.list_hypervisors_detail

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(_schema, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_hypervisor(self, hypervisor_id):
        """Display the details of the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s' % hypervisor_id)
        body = json.loads(body)
        self.validate_response(schema.get_hypervisor, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_servers_on_hypervisor(self, hypervisor_name):
        """List instances belonging to the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/servers' % hypervisor_name)
        body = json.loads(body)
        self.validate_response(schema.get_hypervisors_servers, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_hypervisor_statistics(self):
        """Get hypervisor statistics over all compute nodes."""
        resp, body = self.get('os-hypervisors/statistics')
        body = json.loads(body)
        self.validate_response(schema.get_hypervisor_statistics, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_hypervisor_uptime(self, hypervisor_id):
        """Display the uptime of the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/uptime' % hypervisor_id)
        body = json.loads(body)
        self.validate_response(schema.get_hypervisor_uptime, resp, body)
        return rest_client.ResponseBody(resp, body)

    def search_hypervisor(self, hypervisor_name):  # noqa
        # NOTE: This noqa is for passing T110 check and we cannot rename
        #       to keep backwards compatibility.
        """Search specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/search' % hypervisor_name)
        body = json.loads(body)
        self.validate_response(schema.list_search_hypervisors, resp, body)
        return rest_client.ResponseBody(resp, body)
