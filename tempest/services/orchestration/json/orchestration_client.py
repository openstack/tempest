# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 IBM Corp.
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
import time
import urllib

from tempest.common import rest_client
from tempest import exceptions


class OrchestrationClient(rest_client.RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(OrchestrationClient, self).__init__(config, username, password,
                                                  auth_url, tenant_name)
        self.service = self.config.orchestration.catalog_type
        self.build_interval = self.config.orchestration.build_interval
        self.build_timeout = self.config.orchestration.build_timeout

    def list_stacks(self, params=None):
        """Lists all stacks for a user."""

        uri = 'stacks'
        if params:
            uri += '?%s' % urllib.urlencode(params)

        resp, body = self.get(uri)
        body = json.loads(body)
        return resp, body

    def create_stack(self, name, disable_rollback=True, parameters={},
                     timeout_mins=60, template=None, template_url=None):
        post_body = {
            "stack_name": name,
            "disable_rollback": disable_rollback,
            "parameters": parameters,
            "timeout_mins": timeout_mins,
            "template": "HeatTemplateFormatVersion: '2012-12-12'\n"
        }
        if template:
            post_body['template'] = template
        if template_url:
            post_body['template_url'] = template_url
        body = json.dumps(post_body)
        uri = 'stacks'
        resp, body = self.post(uri, headers=self.headers, body=body)
        return resp, body

    def get_stack(self, stack_identifier):
        """Returns the details of a single stack."""
        url = "stacks/%s" % stack_identifier
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['stack']

    def delete_stack(self, stack_identifier):
        """Deletes the specified Stack."""
        return self.delete("stacks/%s" % str(stack_identifier))

    def wait_for_stack_status(self, stack_identifier, status, failure_status=(
            'CREATE_FAILED',
            'DELETE_FAILED',
            'UPDATE_FAILED',
            'ROLLBACK_FAILED')):
        """Waits for a Volume to reach a given status."""
        stack_status = None
        start = int(time.time())

        while stack_status != status:
            resp, body = self.get_stack(stack_identifier)
            stack_name = body['stack_name']
            stack_status = body['stack_status']
            if stack_status in failure_status:
                raise exceptions.StackBuildErrorException(
                    stack_identifier=stack_identifier,
                    stack_status=stack_status,
                    stack_status_reason=body['stack_status_reason'])

            if int(time.time()) - start >= self.build_timeout:
                message = ('Stack %s failed to reach %s status within '
                           'the required time (%s s).' %
                           (stack_name, status, self.build_timeout))
                raise exceptions.TimeoutException(message)
            time.sleep(self.build_interval)
