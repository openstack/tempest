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

from tempest_lib import exceptions as lib_exc

from tempest.common import service_client
from tempest import exceptions


class OrchestrationClient(service_client.ServiceClient):

    def list_stacks(self, params=None):
        """Lists all stacks for a user."""

        uri = 'stacks'
        if params:
            uri += '?%s' % urllib.urlencode(params)

        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBodyList(resp, body['stacks'])

    def create_stack(self, name, disable_rollback=True, parameters=None,
                     timeout_mins=60, template=None, template_url=None,
                     environment=None, files=None):
        if parameters is None:
            parameters = {}
        headers, body = self._prepare_update_create(
            name,
            disable_rollback,
            parameters,
            timeout_mins,
            template,
            template_url,
            environment,
            files)
        uri = 'stacks'
        resp, body = self.post(uri, headers=headers, body=body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def update_stack(self, stack_identifier, name, disable_rollback=True,
                     parameters=None, timeout_mins=60, template=None,
                     template_url=None, environment=None, files=None):
        if parameters is None:
            parameters = {}
        headers, body = self._prepare_update_create(
            name,
            disable_rollback,
            parameters,
            timeout_mins,
            template,
            template_url,
            environment)

        uri = "stacks/%s" % stack_identifier
        resp, body = self.put(uri, headers=headers, body=body)
        self.expected_success(202, resp.status)
        return service_client.ResponseBody(resp, body)

    def _prepare_update_create(self, name, disable_rollback=True,
                               parameters=None, timeout_mins=60,
                               template=None, template_url=None,
                               environment=None, files=None):
        if parameters is None:
            parameters = {}
        post_body = {
            "stack_name": name,
            "disable_rollback": disable_rollback,
            "parameters": parameters,
            "timeout_mins": timeout_mins,
            "template": "HeatTemplateFormatVersion: '2012-12-12'\n",
            "environment": environment,
            "files": files
        }
        if template:
            post_body['template'] = template
        if template_url:
            post_body['template_url'] = template_url
        body = json.dumps(post_body)

        # Password must be provided on stack create so that heat
        # can perform future operations on behalf of the user
        headers = self.get_headers()
        headers['X-Auth-Key'] = self.password
        headers['X-Auth-User'] = self.user
        return headers, body

    def show_stack(self, stack_identifier):
        """Returns the details of a single stack."""
        url = "stacks/%s" % stack_identifier
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body['stack'])

    def suspend_stack(self, stack_identifier):
        """Suspend a stack."""
        url = 'stacks/%s/actions' % stack_identifier
        body = {'suspend': None}
        resp, body = self.post(url, json.dumps(body))
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp)

    def resume_stack(self, stack_identifier):
        """Resume a stack."""
        url = 'stacks/%s/actions' % stack_identifier
        body = {'resume': None}
        resp, body = self.post(url, json.dumps(body))
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp)

    def list_resources(self, stack_identifier):
        """Returns the details of a single resource."""
        url = "stacks/%s/resources" % stack_identifier
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBodyList(resp, body['resources'])

    def show_resource(self, stack_identifier, resource_name):
        """Returns the details of a single resource."""
        url = "stacks/%s/resources/%s" % (stack_identifier, resource_name)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body['resource'])

    def delete_stack(self, stack_identifier):
        """Deletes the specified Stack."""
        resp, _ = self.delete("stacks/%s" % str(stack_identifier))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def wait_for_resource_status(self, stack_identifier, resource_name,
                                 status, failure_pattern='^.*_FAILED$'):
        """Waits for a Resource to reach a given status."""
        start = int(time.time())
        fail_regexp = re.compile(failure_pattern)

        while True:
            try:
                body = self.show_resource(
                    stack_identifier, resource_name)
            except lib_exc.NotFound:
                # ignore this, as the resource may not have
                # been created yet
                pass
            else:
                resource_name = body['resource_name']
                resource_status = body['resource_status']
                if resource_status == status:
                    return
                if fail_regexp.search(resource_status):
                    raise exceptions.StackResourceBuildErrorException(
                        resource_name=resource_name,
                        stack_identifier=stack_identifier,
                        resource_status=resource_status,
                        resource_status_reason=body['resource_status_reason'])

            if int(time.time()) - start >= self.build_timeout:
                message = ('Resource %s failed to reach %s status '
                           '(current %s) within the required time (%s s).' %
                           (resource_name,
                            status,
                            resource_status,
                            self.build_timeout))
                raise exceptions.TimeoutException(message)
            time.sleep(self.build_interval)

    def wait_for_stack_status(self, stack_identifier, status,
                              failure_pattern='^.*_FAILED$'):
        """Waits for a Stack to reach a given status."""
        start = int(time.time())
        fail_regexp = re.compile(failure_pattern)

        while True:
            try:
                body = self.show_stack(stack_identifier)
            except lib_exc.NotFound:
                if status == 'DELETE_COMPLETE':
                    return
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
                message = ('Stack %s failed to reach %s status (current: %s) '
                           'within the required time (%s s).' %
                           (stack_name, status, stack_status,
                            self.build_timeout))
                raise exceptions.TimeoutException(message)
            time.sleep(self.build_interval)

    def show_resource_metadata(self, stack_identifier, resource_name):
        """Returns the resource's metadata."""
        url = ('stacks/{stack_identifier}/resources/{resource_name}'
               '/metadata'.format(**locals()))
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body['metadata'])

    def list_events(self, stack_identifier):
        """Returns list of all events for a stack."""
        url = 'stacks/{stack_identifier}/events'.format(**locals())
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBodyList(resp, body['events'])

    def list_resource_events(self, stack_identifier, resource_name):
        """Returns list of all events for a resource from stack."""
        url = ('stacks/{stack_identifier}/resources/{resource_name}'
               '/events'.format(**locals()))
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBodyList(resp, body['events'])

    def show_event(self, stack_identifier, resource_name, event_id):
        """Returns the details of a single stack's event."""
        url = ('stacks/{stack_identifier}/resources/{resource_name}/events'
               '/{event_id}'.format(**locals()))
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body['event'])

    def show_template(self, stack_identifier):
        """Returns the template for the stack."""
        url = ('stacks/{stack_identifier}/template'.format(**locals()))
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def _validate_template(self, post_body):
        """Returns the validation request result."""
        post_body = json.dumps(post_body)
        resp, body = self.post('validate', post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def validate_template(self, template, parameters=None):
        """Returns the validation result for a template with parameters."""
        if parameters is None:
            parameters = {}
        post_body = {
            'template': template,
            'parameters': parameters,
        }
        return self._validate_template(post_body)

    def validate_template_url(self, template_url, parameters=None):
        """Returns the validation result for a template with parameters."""
        if parameters is None:
            parameters = {}
        post_body = {
            'template_url': template_url,
            'parameters': parameters,
        }
        return self._validate_template(post_body)

    def list_resource_types(self):
        """List resource types."""
        resp, body = self.get('resource_types')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBodyList(resp, body['resource_types'])

    def show_resource_type(self, resource_type_name):
        """Return the schema of a resource type."""
        url = 'resource_types/%s' % resource_type_name
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, json.loads(body))

    def show_resource_type_template(self, resource_type_name):
        """Return the template of a resource type."""
        url = 'resource_types/%s/template' % resource_type_name
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, json.loads(body))

    def create_software_config(self, name=None, config=None, group=None,
                               inputs=None, outputs=None, options=None):
        headers, body = self._prep_software_config_create(
            name, config, group, inputs, outputs, options)

        url = 'software_configs'
        resp, body = self.post(url, headers=headers, body=body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def show_software_config(self, conf_id):
        """Returns a software configuration resource."""
        url = 'software_configs/%s' % str(conf_id)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_software_config(self, conf_id):
        """Deletes a specific software configuration."""
        url = 'software_configs/%s' % str(conf_id)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def create_software_deploy(self, server_id=None, config_id=None,
                               action=None, status=None,
                               input_values=None, output_values=None,
                               status_reason=None, signal_transport=None):
        """Creates or updates a software deployment."""
        headers, body = self._prep_software_deploy_update(
            None, server_id, config_id, action, status, input_values,
            output_values, status_reason, signal_transport)

        url = 'software_deployments'
        resp, body = self.post(url, headers=headers, body=body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def update_software_deploy(self, deploy_id=None, server_id=None,
                               config_id=None, action=None, status=None,
                               input_values=None, output_values=None,
                               status_reason=None, signal_transport=None):
        """Creates or updates a software deployment."""
        headers, body = self._prep_software_deploy_update(
            deploy_id, server_id, config_id, action, status, input_values,
            output_values, status_reason, signal_transport)

        url = 'software_deployments/%s' % str(deploy_id)
        resp, body = self.put(url, headers=headers, body=body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def list_software_deployments(self):
        """Returns a list of all deployments."""
        url = 'software_deployments'
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def show_software_deployment(self, deploy_id):
        """Returns a specific software deployment."""
        url = 'software_deployments/%s' % str(deploy_id)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def show_software_deployment_metadata(self, server_id):
        """Return a config metadata for a specific server."""
        url = 'software_deployments/metadata/%s' % server_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_software_deploy(self, deploy_id):
        """Deletes a specific software deployment."""
        url = 'software_deployments/%s' % str(deploy_id)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def _prep_software_config_create(self, name=None, conf=None, group=None,
                                     inputs=None, outputs=None, options=None):
        """Prepares a software configuration body."""
        post_body = {}
        if name is not None:
            post_body["name"] = name
        if conf is not None:
            post_body["config"] = conf
        if group is not None:
            post_body["group"] = group
        if inputs is not None:
            post_body["inputs"] = inputs
        if outputs is not None:
            post_body["outputs"] = outputs
        if options is not None:
            post_body["options"] = options
        body = json.dumps(post_body)

        headers = self.get_headers()
        return headers, body

    def _prep_software_deploy_update(self, deploy_id=None, server_id=None,
                                     config_id=None, action=None, status=None,
                                     input_values=None, output_values=None,
                                     status_reason=None,
                                     signal_transport=None):
        """Prepares a deployment create or update (if an id was given)."""
        post_body = {}

        if deploy_id is not None:
            post_body["id"] = deploy_id
        if server_id is not None:
            post_body["server_id"] = server_id
        if config_id is not None:
            post_body["config_id"] = config_id
        if action is not None:
            post_body["action"] = action
        if status is not None:
            post_body["status"] = status
        if input_values is not None:
            post_body["input_values"] = input_values
        if output_values is not None:
            post_body["output_values"] = output_values
        if status_reason is not None:
            post_body["status_reason"] = status_reason
        if signal_transport is not None:
            post_body["signal_transport"] = signal_transport
        body = json.dumps(post_body)

        headers = self.get_headers()
        return headers, body
