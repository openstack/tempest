# Copyright 2021 Red Hat, Inc.
# All rights reserved.
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

from tempest.lib.services.network import base


class LogResourceClient(base.BaseNetworkClient):

    def create_log(self, **kwargs):
        """Creates a log resource.

        Creates a log resource by using the configuration that you define in
        the request object.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-log
        """
        uri = '/log/logs/'
        post_data = {'log': kwargs}
        return self.create_resource(uri, post_data)

    def update_log(self, log_id, **kwargs):
        """Updates a log resource.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-log
        """
        uri = '/log/logs/%s' % log_id
        post_data = {'log': kwargs}
        return self.update_resource(uri, post_data)

    def show_log(self, log_id, **fields):
        """Shows details for a log id.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-log
        """
        uri = '/log/logs/%s' % log_id
        return self.show_resource(uri, **fields)

    def delete_log(self, log_id):
        """Deletes a log resource.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#delete-log
        """
        uri = '/log/logs/%s' % log_id
        return self.delete_resource(uri)

    def list_logs(self, **filters):
        """Lists Logs.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-logs
        """
        uri = '/log/logs'
        return self.list_resources(uri, **filters)
