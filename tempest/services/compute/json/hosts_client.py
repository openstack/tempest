# Copyright 2013 IBM Corp.
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
import urllib

from tempest.api_schema.response.compute.v2_1 import hosts as schema
from tempest.common import service_client


class HostsClientJSON(service_client.ServiceClient):

    def list_hosts(self, params=None):
        """Lists all hosts."""

        url = 'os-hosts'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_hosts, resp, body)
        return service_client.ResponseBodyList(resp, body['hosts'])

    def show_host_detail(self, hostname):
        """Show detail information for the host."""

        resp, body = self.get("os-hosts/%s" % str(hostname))
        body = json.loads(body)
        self.validate_response(schema.get_host_detail, resp, body)
        return service_client.ResponseBodyList(resp, body['host'])

    def update_host(self, hostname, **kwargs):
        """Update a host."""

        request_body = {
            'status': None,
            'maintenance_mode': None,
        }
        request_body.update(**kwargs)
        request_body = json.dumps(request_body)

        resp, body = self.put("os-hosts/%s" % str(hostname), request_body)
        body = json.loads(body)
        self.validate_response(schema.update_host, resp, body)
        return service_client.ResponseBody(resp, body)

    def startup_host(self, hostname):
        """Startup a host."""

        resp, body = self.get("os-hosts/%s/startup" % str(hostname))
        body = json.loads(body)
        self.validate_response(schema.startup_host, resp, body)
        return service_client.ResponseBody(resp, body['host'])

    def shutdown_host(self, hostname):
        """Shutdown a host."""

        resp, body = self.get("os-hosts/%s/shutdown" % str(hostname))
        body = json.loads(body)
        self.validate_response(schema.shutdown_host, resp, body)
        return service_client.ResponseBody(resp, body['host'])

    def reboot_host(self, hostname):
        """reboot a host."""

        resp, body = self.get("os-hosts/%s/reboot" % str(hostname))
        body = json.loads(body)
        self.validate_response(schema.reboot_host, resp, body)
        return service_client.ResponseBody(resp, body['host'])
