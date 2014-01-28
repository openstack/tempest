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
        return resp, body['stacks']

    def create_stack(self, name, disable_rollback=True, parameters={},
                     timeout_mins=60, template=None, template_url=None):
        headers, body = self._prepare_update_create(
            name,
            disable_rollback,
            parameters,
            timeout_mins,
            template,
            template_url)
        uri = 'stacks'
        resp, body = self.post(uri, headers=headers, body=body)
        return resp, body

    def update_stack(self, stack_identifier, name, disable_rollback=True,
                     parameters={}, timeout_mins=60, template=None,
                     template_url=None):
        headers, body = self._prepare_update_create(
            name,
            disable_rollback,
            parameters,
            timeout_mins,
            template,
            template_url)

        uri = "stacks/%s" % stack_identifier
        resp, body = self.put(uri, headers=headers, body=body)
        return resp, body

    def _prepare_update_create(self, name, disable_rollback=True,
                               parameters={}, timeout_mins=60,
                               template=None, template_url=None):
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

        # Password must be provided on stack create so that heat
        # can perform future operations on behalf of the user
        headers = dict(self.headers)
        headers['X-Auth-Key'] = self.password
        headers['X-Auth-User'] = self.user
        return headers, body

    def get_stack(self, stack_identifier):
        """Returns the details of a single stack."""
        url = "stacks/%s" % stack_identifier
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['stack']

    def suspend_stack(self, stack_identifier):
        """Suspend a stack."""
        url = 'stacks/%s/actions' % stack_identifier
        body = {'suspend': None}
        resp, body = self.post(url, json.dumps(body), self.headers)
        return resp, body

    def resume_stack(self, stack_identifier):
        """Resume a stack."""
        url = 'stacks/%s/actions' % stack_identifier
        body = {'resume': None}
        resp, body = self.post(url, json.dumps(body), self.headers)
        return resp, body

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
                resource_name = body['resource_name']
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
                return body
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

    def show_resource_metadata(self, stack_identifier, resource_name):
        """Returns the resource's metadata."""
        url = ('stacks/{stack_identifier}/resources/{resource_name}'
               '/metadata'.format(**locals()))
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['metadata']

    def list_events(self, stack_identifier):
        """Returns list of all events for a stack."""
        url = 'stacks/{stack_identifier}/events'.format(**locals())
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['events']

    def list_resource_events(self, stack_identifier, resource_name):
        """Returns list of all events for a resource from stack."""
        url = ('stacks/{stack_identifier}/resources/{resource_name}'
               '/events'.format(**locals()))
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['events']

    def show_event(self, stack_identifier, resource_name, event_id):
        """Returns the details of a single stack's event."""
        url = ('stacks/{stack_identifier}/resources/{resource_name}/events'
               '/{event_id}'.format(**locals()))
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['event']

    def show_template(self, stack_identifier):
        """Returns the template for the stack."""
        url = ('stacks/{stack_identifier}/template'.format(**locals()))
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def _validate_template(self, post_body):
        """Returns the validation request result."""
        post_body = json.dumps(post_body)
        resp, body = self.post('validate', post_body, self.headers)
        body = json.loads(body)
        return resp, body

    def validate_template(self, template, parameters={}):
        """Returns the validation result for a template with parameters."""
        post_body = {
            'template': template,
            'parameters': parameters,
        }
        return self._validate_template(post_body)

    def validate_template_url(self, template_url, parameters={}):
        """Returns the validation result for a template with parameters."""
        post_body = {
            'template_url': template_url,
            'parameters': parameters,
        }
        return self._validate_template(post_body)
