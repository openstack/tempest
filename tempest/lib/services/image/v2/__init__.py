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

from tempest.lib.services.image.v2.image_members_client import \
    ImageMembersClient
from tempest.lib.services.image.v2.images_client import ImagesClient
from tempest.lib.services.image.v2.namespaces_client import NamespacesClient
from tempest.lib.services.image.v2.resource_types_client import \
    ResourceTypesClient
from tempest.lib.services.image.v2.schemas_client import SchemasClient

__all__ = ['ImageMembersClient', 'ImagesClient', 'NamespacesClient',
           'ResourceTypesClient', 'SchemasClient']
