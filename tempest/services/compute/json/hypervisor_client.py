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

import json

from tempest.api_schema.response.compute.v2_1 import hypervisors as schema
from tempest.common import service_client


class HypervisorClient(service_client.ServiceClient):

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
        return service_client.ResponseBodyList(resp, body['hypervisors'])

    def show_hypervisor(self, hyper_id):
        """Display the details of the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s' % hyper_id)
        body = json.loads(body)
        self.validate_response(schema.get_hypervisor, resp, body)
        return service_client.ResponseBody(resp, body['hypervisor'])

    def list_servers_on_hypervisor(self, hyper_name):
        """List instances belonging to the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/servers' % hyper_name)
        body = json.loads(body)
        self.validate_response(schema.get_hypervisors_servers, resp, body)
        return service_client.ResponseBodyList(resp, body['hypervisors'])

    def show_hypervisor_statistics(self):
        """Get hypervisor statistics over all compute nodes."""
        resp, body = self.get('os-hypervisors/statistics')
        body = json.loads(body)
        self.validate_response(schema.get_hypervisor_statistics, resp, body)
        return service_client.ResponseBody(resp, body['hypervisor_statistics'])

    def show_hypervisor_uptime(self, hyper_id):
        """Display the uptime of the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/uptime' % hyper_id)
        body = json.loads(body)
        self.validate_response(schema.get_hypervisor_uptime, resp, body)
        return service_client.ResponseBody(resp, body['hypervisor'])

    def search_hypervisor(self, hyper_name):
        """Search specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/search' % hyper_name)
        body = json.loads(body)
        self.validate_response(schema.list_search_hypervisors, resp, body)
        return service_client.ResponseBodyList(resp, body['hypervisors'])
