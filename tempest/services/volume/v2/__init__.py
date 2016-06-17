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

from tempest.services.volume.v2.json.admin.hosts_client import HostsClient
from tempest.services.volume.v2.json.admin.quotas_client import QuotasClient
from tempest.services.volume.v2.json.admin.services_client import \
    ServicesClient
from tempest.services.volume.v2.json.admin.types_client import TypesClient
from tempest.services.volume.v2.json.availability_zone_client import \
    AvailabilityZoneClient
from tempest.services.volume.v2.json.backups_client import BackupsClient
from tempest.services.volume.v2.json.extensions_client import ExtensionsClient
from tempest.services.volume.v2.json.qos_client import QosSpecsClient
from tempest.services.volume.v2.json.snapshots_client import SnapshotsClient
from tempest.services.volume.v2.json.volumes_client import VolumesClient

__all__ = ['HostsClient', 'QuotasClient', 'ServicesClient', 'TypesClient',
           'AvailabilityZoneClient', 'BackupsClient', 'ExtensionsClient',
           'QosSpecsClient', 'SnapshotsClient', 'VolumesClient']
