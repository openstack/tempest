# Copyright 2015 NEC Corporation.  All rights reserved.
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


class QuotasClient(base.BaseNetworkClient):

    def update_quotas(self, tenant_id, **kwargs):
        """Update quota for a project.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/index.html#update-quota-for-a-project
        """
        put_body = {'quota': kwargs}
        uri = '/quotas/%s' % tenant_id
        return self.update_resource(uri, put_body)

    def reset_quotas(self, tenant_id):  # noqa
        # NOTE: This noqa is for passing T111 check and we cannot rename
        #       to keep backwards compatibility.
        uri = '/quotas/%s' % tenant_id
        return self.delete_resource(uri)

    def show_quotas(self, tenant_id, **fields):
        uri = '/quotas/%s' % tenant_id
        return self.show_resource(uri, **fields)

    def list_quotas(self, **filters):
        uri = '/quotas'
        return self.list_resources(uri, **filters)

    def show_default_quotas(self, tenant_id):
        """List default quotas for a project."""
        uri = '/quotas/%s/default' % tenant_id
        return self.show_resource(uri)
