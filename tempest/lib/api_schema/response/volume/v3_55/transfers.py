# Copyright 2022 Red Hat, Inc.
# All rights reserved.
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

from tempest.lib.api_schema.response.volume import transfers

# Volume microversion 3.55:
# Add 'no_snapshots' attribute in 'transfer' responses.

create_volume_transfer = copy.deepcopy(transfers.create_volume_transfer)
create_volume_transfer['response_body']['properties']['transfer'][
    'properties'].update({'no_snapshots': {'type': 'boolean'}})

common_show_volume_transfer = copy.deepcopy(
    transfers.common_show_volume_transfer)
common_show_volume_transfer['properties'].update(
    {'no_snapshots': {'type': 'boolean'}})

show_volume_transfer = copy.deepcopy(transfers.show_volume_transfer)
show_volume_transfer['response_body']['properties'][
    'transfer'] = common_show_volume_transfer

list_volume_transfers_no_detail = copy.deepcopy(
    transfers.list_volume_transfers_no_detail)

list_volume_transfers_with_detail = copy.deepcopy(
    transfers.list_volume_transfers_with_detail)
list_volume_transfers_with_detail['response_body']['properties']['transfers'][
    'items'] = common_show_volume_transfer

delete_volume_transfer = copy.deepcopy(transfers.delete_volume_transfer)

accept_volume_transfer = copy.deepcopy(transfers.accept_volume_transfer)
