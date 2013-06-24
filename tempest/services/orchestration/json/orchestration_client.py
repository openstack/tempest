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
import re
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

        # Password must be provided on stack create so that heat
        # can perform future operations on behalf of the user
        headers = dict(self.headers)
        headers['X-Auth-Key'] = self.password
        headers['X-Auth-User'] = self.user

        resp, body = self.post(uri, headers=headers, body=body)
        return resp, body

    def get_stack(self, stack_identifier):
        """Returns the details of a single stack."""
        url = "stacks/%s" % stack_identifier
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['stack']

    def list_resources(self, stack_identifier):
        """Returns the details of a single resource."""
        url = "stacks/%s/resources" % stack_identifier
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['resources']

    def get_resource(self, stack_identifier, resource_name):
        """Returns the details of a single resource."""
        url = "stacks/%s/resources/%s" % (stack_identifier, resource_name)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['resource']

    def delete_stack(self, stack_identifier):
        """Deletes the specified Stack."""
        return self.delete("stacks/%s" % str(stack_identifier))

    def wait_for_resource_status(self, stack_identifier, resource_name,
                                 status, failure_pattern='^.*_FAILED$'):
        """Waits for a Resource to reach a given status."""
        start = int(time.time())
        fail_regexp = re.compile(failure_pattern)

        while True:
            try:
                resp, body = self.get_resource(
                    stack_identifier, resource_name)
            except exceptions.NotFound:
                # ignore this, as the resource may not have
                # been created yet
                pass
            else:
                resource_name = body['logical_resource_id']
                resource_status = body['resource_status']
                if resource_status == status:
                    return
                if fail_regexp.search(resource_status):
                    raise exceptions.StackBuildErrorException(
                        stack_identifier=stack_identifier,
                        resource_status=resource_status,
                        resource_status_reason=body['resource_status_reason'])

            if int(time.time()) - start >= self.build_timeout:
                message = ('Resource %s failed to reach %s status within '
                           'the required time (%s s).' %
                           (resource_name, status, self.build_timeout))
                raise exceptions.TimeoutException(message)
            time.sleep(self.build_interval)

    def wait_for_stack_status(self, stack_identifier, status,
                              failure_pattern='^.*_FAILED$'):
        """Waits for a Stack to reach a given status."""
        start = int(time.time())
        fail_regexp = re.compile(failure_pattern)

        while True:
            resp, body = self.get_stack(stack_identifier)
            stack_name = body['stack_name']
            stack_status = body['stack_status']
            if stack_status == status:
                return
            if fail_regexp.search(stack_status):
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
