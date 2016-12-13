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

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.api_schema.response.compute.v2_1 import hosts as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class HostsClient(base_compute_client.BaseComputeClient):

    def list_hosts(self, **params):
        """List all hosts."""

        url = 'os-hosts'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_hosts, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_host(self, hostname):
        """Show detail information for the host."""

        resp, body = self.get("os-hosts/%s" % hostname)
        body = json.loads(body)
        self.validate_response(schema.get_host_detail, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_host(self, hostname, **kwargs):
        """Update a host.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#enablehost
        """

        request_body = {
            'status': None,
            'maintenance_mode': None,
        }
        request_body.update(**kwargs)
        request_body = json.dumps(request_body)

        resp, body = self.put("os-hosts/%s" % hostname, request_body)
        body = json.loads(body)
        self.validate_response(schema.update_host, resp, body)
        return rest_client.ResponseBody(resp, body)

    def startup_host(self, hostname):  # noqa
        # NOTE: This noqa is for passing T110 check and we cannot rename
        #       to keep backwards compatibility. Actually, the root problem
        #       of this is a wrong API design. GET operation should not change
        #       resource status, but current API does that.
        """Startup a host."""

        resp, body = self.get("os-hosts/%s/startup" % hostname)
        body = json.loads(body)
        self.validate_response(schema.startup_host, resp, body)
        return rest_client.ResponseBody(resp, body)

    def shutdown_host(self, hostname):  # noqa
        # NOTE: This noqa is for passing T110 check and we cannot rename
        #       to keep backwards compatibility. Actually, the root problem
        #       of this is a wrong API design. GET operation should not change
        #       resource status, but current API does that.
        """Shutdown a host."""

        resp, body = self.get("os-hosts/%s/shutdown" % hostname)
        body = json.loads(body)
        self.validate_response(schema.shutdown_host, resp, body)
        return rest_client.ResponseBody(resp, body)

    def reboot_host(self, hostname):  # noqa
        # NOTE: This noqa is for passing T110 check and we cannot rename
        #       to keep backwards compatibility. Actually, the root problem
        #       of this is a wrong API design. GET operation should not change
        #       resource status, but current API does that.
        """Reboot a host."""

        resp, body = self.get("os-hosts/%s/reboot" % hostname)
        body = json.loads(body)
        self.validate_response(schema.reboot_host, resp, body)
        return rest_client.ResponseBody(resp, body)
