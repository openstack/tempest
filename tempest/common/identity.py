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

from tempest import config
from tempest.lib.common import cred_client
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


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


def identity_utils(clients):
    """A client that abstracts v2 and v3 identity operations.

    This can be used for creating and tearing down projects in tests. It
    should not be used for testing identity features.

    :param clients: a client manager.
    :return
    """
    if CONF.identity.auth_version == 'v2':
        client = clients.identity_client
        users_client = clients.users_client
        project_client = clients.tenants_client
        roles_client = clients.roles_client
        domains_client = None
    else:
        client = clients.identity_v3_client
        users_client = clients.users_v3_client
        project_client = clients.projects_client
        roles_client = clients.roles_v3_client
        domains_client = clients.domains_client

    try:
        domain = client.auth_provider.credentials.project_domain_name
    except AttributeError:
        domain = CONF.auth.default_credentials_domain_name

    return cred_client.get_creds_client(client, project_client,
                                        users_client,
                                        roles_client,
                                        domains_client,
                                        project_domain_name=domain)
