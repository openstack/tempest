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

from tempest.api_schema.response.compute import hypervisors as common_schema
from tempest.api_schema.response.compute.v2 import hypervisors as v2schema
from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class HypervisorClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(HypervisorClientJSON, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def get_hypervisor_list(self):
        """List hypervisors information."""
        resp, body = self.get('os-hypervisors')
        body = json.loads(body)
        self.validate_response(common_schema.common_hypervisors_detail,
                               resp, body)
        return resp, body['hypervisors']

    def get_hypervisor_list_details(self):
        """Show detailed hypervisors information."""
        resp, body = self.get('os-hypervisors/detail')
        body = json.loads(body)
        self.validate_response(common_schema.common_list_hypervisors_detail,
                               resp, body)
        return resp, body['hypervisors']

    def get_hypervisor_show_details(self, hyper_id):
        """Display the details of the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s' % hyper_id)
        body = json.loads(body)
        self.validate_response(common_schema.common_show_hypervisor,
                               resp, body)
        return resp, body['hypervisor']

    def get_hypervisor_servers(self, hyper_name):
        """List instances belonging to the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/servers' % hyper_name)
        body = json.loads(body)
        self.validate_response(v2schema.hypervisors_servers, resp, body)
        return resp, body['hypervisors']

    def get_hypervisor_stats(self):
        """Get hypervisor statistics over all compute nodes."""
        resp, body = self.get('os-hypervisors/statistics')
        body = json.loads(body)
        self.validate_response(common_schema.hypervisor_statistics, resp, body)
        return resp, body['hypervisor_statistics']

    def get_hypervisor_uptime(self, hyper_id):
        """Display the uptime of the specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/uptime' % hyper_id)
        body = json.loads(body)
        self.validate_response(common_schema.hypervisor_uptime, resp, body)
        return resp, body['hypervisor']

    def search_hypervisor(self, hyper_name):
        """Search specified hypervisor."""
        resp, body = self.get('os-hypervisors/%s/search' % hyper_name)
        body = json.loads(body)
        self.validate_response(common_schema.common_hypervisors_detail,
                               resp, body)
        return resp, body['hypervisors']
