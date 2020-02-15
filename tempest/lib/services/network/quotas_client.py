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

import functools

from tempest.lib.services.network import base


def _warning_deprecate_tenant_id(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        _self = args[0]
        # check length of arg to know whether 'tenant_id' is passed as
        # positional arg or kwargs.
        if len(args) < 2:
            if 'tenant_id' in kwargs:
                _self.LOG.warning(
                    'positional arg name "tenant_id" is deprecated, for '
                    'removal, please start using "project_id" instead')
            elif 'project_id' in kwargs:
                # fallback to deprecated name till deprecation phase.
                kwargs['tenant_id'] = kwargs.pop('project_id')

        return func(*args, **kwargs)
    return inner


class QuotasClient(base.BaseNetworkClient):

    @_warning_deprecate_tenant_id
    def update_quotas(self, tenant_id, **kwargs):
        """Update quota for a project.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-quota-for-a-project
        """
        put_body = {'quota': kwargs}
        uri = '/quotas/%s' % tenant_id
        return self.update_resource(uri, put_body)

    @_warning_deprecate_tenant_id
    def reset_quotas(self, tenant_id):  # noqa
        # NOTE: This noqa is for passing T111 check and we cannot rename
        #       to keep backwards compatibility.
        uri = '/quotas/%s' % tenant_id
        return self.delete_resource(uri)

    @_warning_deprecate_tenant_id
    def show_quotas(self, tenant_id, **fields):
        """Show quota for a project.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-quotas-for-a-project
        """
        uri = '/quotas/%s' % tenant_id
        return self.show_resource(uri, **fields)

    def list_quotas(self, **filters):
        """List quotas for projects with non default quota values.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-quotas-for-projects-with-non-default-quota-values
        """
        uri = '/quotas'
        return self.list_resources(uri, **filters)

    @_warning_deprecate_tenant_id
    def show_default_quotas(self, tenant_id):
        """List default quotas for a project."""
        uri = '/quotas/%s/default' % tenant_id
        return self.show_resource(uri)

    @_warning_deprecate_tenant_id
    def show_quota_details(self, tenant_id):
        """Show quota details for a project."""
        uri = '/quotas/%s/details.json' % tenant_id
        return self.show_resource(uri)
