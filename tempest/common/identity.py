# Copyright 2015 NEC Corporation
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

from tempest.lib import exceptions as lib_exc


def get_tenant_by_name(client, tenant_name):
    tenants = client.list_tenants()['tenants']
    for tenant in tenants:
        if tenant['name'] == tenant_name:
            return tenant
    raise lib_exc.NotFound('No such tenant(%s) in %s' % (tenant_name, tenants))


def get_user_by_username(client, tenant_id, username):
    users = client.list_tenant_users(tenant_id)['users']
    for user in users:
        if user['name'] == username:
            return user
    raise lib_exc.NotFound('No such user(%s) in %s' % (username, users))
