# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

import time

from tempest_lib import exceptions as lib_exc

from tempest import exceptions
from tempest import config
from tempest.services.volume.json.volumes_client import BaseVolumesClientJSON
from tempest.services.volume.json.snapshots_client import BaseSnapshotsClientJSON

CONF = config.CONF

class CleanBFVResource(BaseVolumesClientJSON, BaseSnapshotsClientJSON):
    """
    Client class to clean up the resources created due to boot from volume
    feature. This cleanup will delete any snapshot attached to volume from
    which VM was booted and then volume itself.
    """
    def __init__(self, auth_provider, **kwargs):
        BaseVolumesClientJSON.__init__(self, auth_provider,
          default_volume_size=CONF.volume.volume_size, **kwargs)
        BaseSnapshotsClientJSON.__init__(self, auth_provider, **kwargs)
        

    def _wait_for_snapshot_deletion(self, snapshot_id):
        """Waits for a Snapshot to reach a given status."""
        start_time = time.time()
        while True:
            try:
                self.show_snapshot(snapshot_id)
            except lib_exc.NotFound:
                return
            else: 
                time.sleep(self.build_interval)
                dtime = time.time() - start_time
                if dtime > self.build_timeout:
                    message = ('Time Limit Exceeded! (%ds)'
                               'while waiting for snapshot %s to get deleted.'
                               % (self.build_timeout, snapshot_id))
                    raise exceptions.TimeoutException(message)

    def _delete_attached_snapshots(self,volume_id):
        self.bfv_snapshots = self.list_snapshots()
        for snapshot in self.bfv_snapshots:
            if snapshot['volume_id'] == volume_id:
                self.delete_snapshot(snapshot['id'])
                self._wait_for_snapshot_deletion(snapshot['id'])
                self.bfv_snapshots.remove(snapshot)

    def volume_not_deletable(self, volume):
        """This will return true if either volume does not exist
        or in available or error state."""
        try:
            res = self.show_volume(volume)
            if res['status'] not in ['available', 'error']:
                return True
        except lib_exc.NotFound:
            return True
        return False

    def clean_bfv_resource(self, volumes):
        """First clean snapshots attached to volume if any then delete volume.
        """
        for volume in volumes:
            if not volume or self.volume_not_deletable(volume):
                continue
            self._delete_attached_snapshots(volume)
            self.delete_volume(volume)

def set_block_device_mapping_args(image_ref, kwargs):
    """
    Update the kwargs dictionary with block device mapping.
    These arguments are required when booting instance from volume.
    """
    if "block_device_mapping_v2" in kwargs.keys() or \
       "block_device_mapping" in kwargs.keys():
        return kwargs
    if 'volume_size' in kwargs:
        vol_size = kwargs.pop('volume_size')
    else:
        vol_size = CONF.volume.volume_size
    bv_map = [{
            "source_type": "image",
            "destination_type": "volume",
            "delete_on_termination": "1",
            "boot_index": 0,
            "uuid": image_ref,
            "device_name": "vda",
            "volume_size": str(vol_size)}]
    bdm_args = {
    'block_device_mapping_v2' : bv_map,
    }
    kwargs.update(bdm_args)
    return kwargs

def get_cleanBFV_obj(auth_provider):
    default_params = {
        'disable_ssl_certificate_validation':
            CONF.identity.disable_ssl_certificate_validation,
        'ca_certs': CONF.identity.ca_certificates_file,
        'trace_requests': CONF.debug.trace_requests
    }
    params = {
        'service': CONF.volume.catalog_type,
        'region': CONF.volume.region or CONF.identity.region,
        'endpoint_type': CONF.volume.endpoint_type,
        'build_interval': CONF.volume.build_interval,
        'build_timeout': CONF.volume.build_timeout
    }
    params.update(default_params)
    CleanBFVResource(auth_provider, **params)

