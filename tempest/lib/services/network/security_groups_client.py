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

from tempest.lib import exceptions as lib_exc
from tempest.lib.services.network import base


class SecurityGroupsClient(base.BaseNetworkClient):

    def create_security_group(self, **kwargs):
        """Creates an OpenStack Networking security group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-security-group
        """
        uri = '/security-groups'
        post_data = {'security_group': kwargs}
        return self.create_resource(uri, post_data)

    def update_security_group(self, security_group_id, **kwargs):
        """Updates a security group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-security-group
        """
        uri = '/security-groups/%s' % security_group_id
        post_data = {'security_group': kwargs}
        return self.update_resource(uri, post_data)

    def show_security_group(self, security_group_id, **fields):
        """Shows details for a security group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-security-group
        """
        uri = '/security-groups/%s' % security_group_id
        return self.show_resource(uri, **fields)

    def delete_security_group(self, security_group_id):
        """Deletes an OpenStack Networking security group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#delete-security-group
        """
        uri = '/security-groups/%s' % security_group_id
        return self.delete_resource(uri)

    def list_security_groups(self, **filters):
        """Lists OpenStack Networking security groups.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-security-groups
        """
        uri = '/security-groups'
        return self.list_resources(uri, **filters)

    def is_resource_deleted(self, id):
        try:
            self.show_security_group(id)
        except lib_exc.NotFound:
            return True
        return False
