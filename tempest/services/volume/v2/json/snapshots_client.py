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

from tempest.services.volume.base import base_snapshots_client


class SnapshotsClient(base_snapshots_client.BaseSnapshotsClient):
    """Client class to send CRUD Volume V2 API requests."""
    api_version = "v2"
    create_resp = 202
