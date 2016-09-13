# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from tempest.lib.services.identity.v2.endpoints_client import EndpointsClient
from tempest.lib.services.identity.v2.identity_client import IdentityClient
from tempest.lib.services.identity.v2.roles_client import RolesClient
from tempest.lib.services.identity.v2.services_client import ServicesClient
from tempest.lib.services.identity.v2.tenants_client import TenantsClient
from tempest.lib.services.identity.v2.token_client import TokenClient
from tempest.lib.services.identity.v2.users_client import UsersClient

__all__ = ['EndpointsClient', 'IdentityClient', 'RolesClient',
           'ServicesClient', 'TenantsClient', 'TokenClient', 'UsersClient']
