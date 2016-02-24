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


class SecurityGroupsClient(base.BaseNetworkClient):

    def create_security_group(self, **kwargs):
        uri = '/security-groups'
        post_data = {'security_group': kwargs}
        return self.create_resource(uri, post_data)

    def update_security_group(self, security_group_id, **kwargs):
        uri = '/security-groups/%s' % security_group_id
        post_data = {'security_group': kwargs}
        return self.update_resource(uri, post_data)

    def show_security_group(self, security_group_id, **fields):
        uri = '/security-groups/%s' % security_group_id
        return self.show_resource(uri, **fields)

    def delete_security_group(self, security_group_id):
        uri = '/security-groups/%s' % security_group_id
        return self.delete_resource(uri)

    def list_security_groups(self, **filters):
        uri = '/security-groups'
        return self.list_resources(uri, **filters)
