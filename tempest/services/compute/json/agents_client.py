# Copyright 2014 NEC Corporation.  All rights reserved.
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

from tempest.api_schema.response.compute.v2_1 import agents as schema
from tempest.common import service_client


class AgentsClient(service_client.ServiceClient):
    """
    Tests Agents API
    """

    def list_agents(self, **params):
        """List all agent builds."""
        url = 'os-agents'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_agents, resp, body)
        return service_client.ResponseBody(resp, body)

    def create_agent(self, **kwargs):
        """Create an agent build."""
        post_body = json.dumps({'agent': kwargs})
        resp, body = self.post('os-agents', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_agent, resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_agent(self, agent_id):
        """Delete an existing agent build."""
        resp, body = self.delete("os-agents/%s" % agent_id)
        self.validate_response(schema.delete_agent, resp, body)
        return service_client.ResponseBody(resp, body)

    def update_agent(self, agent_id, **kwargs):
        """Update an agent build."""
        put_body = json.dumps({'para': kwargs})
        resp, body = self.put('os-agents/%s' % agent_id, put_body)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)
