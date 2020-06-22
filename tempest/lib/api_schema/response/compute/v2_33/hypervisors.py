# Copyright 2018 ZTE Corporation.  All rights reserved.
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

import copy

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types
from tempest.lib.api_schema.response.compute.v2_28 \
    import hypervisors as hypervisorsv228

###########################################################################
#
# 2.33:
#
# hypervisor_links parameter is added to the response body for the following
# APIs:
#
# - GET /os-hypervisors
# - GET /os-hypervisors/detail
###########################################################################
list_search_hypervisors = copy.deepcopy(
    hypervisorsv228.list_search_hypervisors)
list_search_hypervisors['response_body']['properties'].update(
    {'hypervisors_links': parameter_types.links}
)

list_hypervisors_detail = copy.deepcopy(
    hypervisorsv228.list_hypervisors_detail)
list_hypervisors_detail['response_body']['properties'].update(
    {'hypervisors_links': parameter_types.links}
)

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.28 ***
get_hypervisor = copy.deepcopy(hypervisorsv228.get_hypervisor)
hypervisor_detail = copy.deepcopy(hypervisorsv228.hypervisor_detail)
get_hypervisor_statistics = \
    copy.deepcopy(hypervisorsv228.get_hypervisor_statistics)
get_hypervisor_uptime = copy.deepcopy(hypervisorsv228.get_hypervisor_uptime)
get_hypervisors_servers = copy.deepcopy(
    hypervisorsv228.get_hypervisors_servers)
