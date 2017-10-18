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

from tempest.lib.services.object_storage.account_client import AccountClient
from tempest.lib.services.object_storage.bulk_middleware_client import \
    BulkMiddlewareClient
from tempest.lib.services.object_storage.capabilities_client import \
    CapabilitiesClient
from tempest.lib.services.object_storage.container_client import \
    ContainerClient
from tempest.lib.services.object_storage.object_client import ObjectClient

__all__ = ['AccountClient', 'BulkMiddlewareClient', 'CapabilitiesClient',
           'ContainerClient', 'ObjectClient']
