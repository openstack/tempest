# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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

from tempest.common.rest_client import RestClient


class HostsV3ClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(HostsV3ClientJSON, self).__init__(config, username, password,
                                                auth_url, tenant_name)
        self.service = self.config.compute.catalog_v3_type

    def list_hosts(self, params=None):
        """Lists all hosts."""

        url = 'os-hosts'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['hosts']

    def show_host_detail(self, hostname):
        """Show detail information for the host."""

        resp, body = self.get("os-hosts/%s" % str(hostname))
        body = json.loads(body)
        return resp, body['host']

    def update_host(self, hostname, **kwargs):
        """Update a host."""

        request_body = {
            'status': None,
            'maintenance_mode': None,
        }
        request_body.update(**kwargs)
        request_body = json.dumps({'host': request_body})

        resp, body = self.put("os-hosts/%s" % str(hostname), request_body,
                              self.headers)
        body = json.loads(body)
        return resp, body

    def startup_host(self, hostname):
        """Startup a host."""

        resp, body = self.get("os-hosts/%s/startup" % str(hostname))
        body = json.loads(body)
        return resp, body['host']

    def shutdown_host(self, hostname):
        """Shutdown a host."""

        resp, body = self.get("os-hosts/%s/shutdown" % str(hostname))
        body = json.loads(body)
        return resp, body['host']

    def reboot_host(self, hostname):
        """reboot a host."""

        resp, body = self.get("os-hosts/%s/reboot" % str(hostname))
        body = json.loads(body)
        return resp, body['host']
