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

from tempest.lib.services.volume.v1.availability_zone_client \
    import AvailabilityZoneClient
from tempest.lib.services.volume.v1.backups_client import BackupsClient
from tempest.lib.services.volume.v1.encryption_types_client import \
    EncryptionTypesClient
from tempest.lib.services.volume.v1.extensions_client import ExtensionsClient
from tempest.lib.services.volume.v1.hosts_client import HostsClient
from tempest.lib.services.volume.v1.limits_client import LimitsClient
from tempest.lib.services.volume.v1.qos_client import QosSpecsClient
from tempest.lib.services.volume.v1.quotas_client import QuotasClient
from tempest.lib.services.volume.v1.services_client import ServicesClient
from tempest.lib.services.volume.v1.snapshots_client import SnapshotsClient
from tempest.lib.services.volume.v1.types_client import TypesClient
from tempest.lib.services.volume.v1.volumes_client import VolumesClient

__all__ = ['AvailabilityZoneClient', 'BackupsClient', 'EncryptionTypesClient',
           'ExtensionsClient', 'HostsClient', 'QosSpecsClient', 'QuotasClient',
           'ServicesClient', 'SnapshotsClient', 'TypesClient', 'VolumesClient',
           'LimitsClient']
