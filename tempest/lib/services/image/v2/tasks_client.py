# Copyright 2023 Red Hat, Inc.
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


from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client

CHUNKSIZE = 1024 * 64  # 64kB


class TaskClient(rest_client.RestClient):
    api_version = "v2"

    def create_task(self, **kwargs):
        """Create a task.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/image/v2/#create-task
        """
        data = json.dumps(kwargs)
        resp, body = self.post('tasks', data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_tasks(self, **kwargs):
        """List tasks.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/image/v2/#list-tasks
        """
        url = 'tasks'

        if kwargs:
            url += '?%s' % urllib.urlencode(kwargs)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_tasks(self, task_id):
        """Show task details.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#show-task-details
        """
        url = 'tasks/%s' % task_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
