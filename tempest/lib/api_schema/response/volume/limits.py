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

show_limits = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'limits': {
                'type': 'object',
                'properties': {
                    'rate': {'type': 'array'},
                    'absolute': {
                        'type': 'object',
                        'properties': {
                            'totalSnapshotsUsed': {'type': 'integer'},
                            'maxTotalBackups': {'type': 'integer'},
                            'maxTotalVolumeGigabytes': {'type': 'integer'},
                            'maxTotalSnapshots': {'type': 'integer'},
                            'maxTotalBackupGigabytes': {'type': 'integer'},
                            'totalBackupGigabytesUsed': {'type': 'integer'},
                            'maxTotalVolumes': {'type': 'integer'},
                            'totalVolumesUsed': {'type': 'integer'},
                            'totalBackupsUsed': {'type': 'integer'},
                            'totalGigabytesUsed': {'type': 'integer'},
                        },
                        'additionalProperties': False,
                        'required': ['totalSnapshotsUsed', 'maxTotalBackups',
                                     'maxTotalVolumeGigabytes',
                                     'maxTotalSnapshots',
                                     'maxTotalBackupGigabytes',
                                     'totalBackupGigabytesUsed',
                                     'maxTotalVolumes', 'totalVolumesUsed',
                                     'totalBackupsUsed', 'totalGigabytesUsed']
                    }
                },
                'additionalProperties': False,
                'required': ['rate', 'absolute'],
            }
        },
        'additionalProperties': False,
        'required': ['limits']
    }
}
