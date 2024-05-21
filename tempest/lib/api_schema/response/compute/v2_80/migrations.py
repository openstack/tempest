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

import copy

from tempest.lib.api_schema.response.compute.v2_59 import migrations

###########################################################################
#
# 2.80:
#
# The user_id and project_id value is now returned in the response body in
# addition to the migration id for the following API responses:
#
# - GET /os-migrations
#
###########################################################################

user_id = {'type': 'string'}
project_id = {'type': 'string'}

list_migrations = copy.deepcopy(migrations.list_migrations)

list_migrations['response_body']['properties']['migrations']['items'][
    'properties'].update({
        'user_id': user_id,
        'project_id': project_id
    })

list_migrations['response_body']['properties']['migrations']['items'][
    'required'].extend(['user_id', 'project_id'])
