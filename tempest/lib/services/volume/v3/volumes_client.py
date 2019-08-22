# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

from oslo_serialization import jsonutils as json
import six
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.volume import base_client


class VolumesClient(base_client.BaseClient):
    """Client class to send CRUD Volume V3 API requests"""

    def _prepare_params(self, params):
        """Prepares params for use in get or _ext_get methods.

        If params is a string it will be left as it is, but if it's not it will
        be urlencoded.
        """
        if isinstance(params, six.string_types):
            return params
        return urllib.urlencode(params)

    def list_hosts(self):
        """Lists all hosts summary info that is not disabled.

        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-all-hosts-for-a-project
        """
        resp, body = self.get('os-hosts')
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_volumes(self, detail=False, params=None):
        """List all the volumes created.

        Params can be a string (must be urlencoded) or a dictionary.
        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-accessible-volumes-with-details
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-accessible-volumes
        """
        url = 'volumes'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % self._prepare_params(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def migrate_volume(self, volume_id, **kwargs):
        """Migrate a volume to a new backend

        For a full list of available parameters please refer to the offical
        API reference:

        https://docs.openstack.org/api-ref/block-storage/v3/index.html#migrate-a-volume
        """
        post_body = json.dumps({'os-migrate_volume': kwargs})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume(self, volume_id):
        """Returns the details of a single volume."""
        url = "volumes/%s" % volume_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_volume(self, **kwargs):
        """Creates a new Volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#create-a-volume
        """
        post_body = json.dumps({'volume': kwargs})
        resp, body = self.post('volumes', post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume(self, volume_id, **kwargs):
        """Updates the Specified Volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#update-a-volume
        """
        put_body = json.dumps({'volume': kwargs})
        resp, body = self.put('volumes/%s' % volume_id, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume(self, volume_id, **params):
        """Deletes the Specified Volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#delete-a-volume
        """
        url = 'volumes/%s' % volume_id
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.delete(url)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume_summary(self, **params):
        """Get volumes summary.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#get-volumes-summary
        """
        url = 'volumes/summary'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def upload_volume(self, volume_id, **kwargs):
        """Uploads a volume in Glance.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#upload-volume-to-image
        """
        post_body = json.dumps({'os-volume_upload_image': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def attach_volume(self, volume_id, **kwargs):
        """Attaches a volume to a given instance on a given mountpoint.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#attach-volume-to-a-server
        """
        post_body = json.dumps({'os-attach': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def set_bootable_volume(self, volume_id, **kwargs):
        """Set a bootable flag for a volume - true or false.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#update-a-volume-s-bootable-status
        """
        post_body = json.dumps({'os-set_bootable': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def detach_volume(self, volume_id):
        """Detaches a volume from an instance."""
        post_body = json.dumps({'os-detach': {}})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reserve_volume(self, volume_id):
        """Reserves a volume."""
        post_body = json.dumps({'os-reserve': {}})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def unreserve_volume(self, volume_id):
        """Restore a reserved volume ."""
        post_body = json.dumps({'os-unreserve': {}})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        """Check the specified resource is deleted or not.

        :param id: A checked resource id
        :raises lib_exc.DeleteErrorException: If the specified resource is on
            the status the delete was failed.
        """
        try:
            volume = self.show_volume(id)
        except lib_exc.NotFound:
            return True
        if volume["volume"]["status"] == "error_deleting":
            raise lib_exc.DeleteErrorException(
                "Volume %s failed to delete and is in error_deleting status" %
                volume['id'])
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'volume'

    def extend_volume(self, volume_id, **kwargs):
        """Extend a volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#extend-a-volume-size
        """
        post_body = json.dumps({'os-extend': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reset_volume_status(self, volume_id, **kwargs):
        """Reset the Specified Volume's Status.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#reset-a-volume-s-statuses
        """
        post_body = json.dumps({'os-reset_status': kwargs})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_readonly(self, volume_id, **kwargs):
        """Update the Specified Volume readonly.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#updates-volume-read-only-access-mode-flag
        """
        post_body = json.dumps({'os-update_readonly_flag': kwargs})
        url = 'volumes/%s/action' % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def force_delete_volume(self, volume_id):
        """Force Delete Volume."""
        post_body = json.dumps({'os-force_delete': {}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_volume_metadata(self, volume_id, metadata):
        """Create metadata for the volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#create-metadata-for-volume
        """
        put_body = json.dumps({'metadata': metadata})
        url = "volumes/%s/metadata" % volume_id
        resp, body = self.post(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume_metadata(self, volume_id):
        """Get metadata of the volume."""
        url = "volumes/%s/metadata" % volume_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_metadata(self, volume_id, metadata):
        """Update metadata for the volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#update-a-volume-s-metadata
        """
        put_body = json.dumps({'metadata': metadata})
        url = "volumes/%s/metadata" % volume_id
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume_metadata_item(self, volume_id, id):
        """Show metadata item for the volume."""
        url = "volumes/%s/metadata/%s" % (volume_id, id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_metadata_item(self, volume_id, id, meta_item):
        """Update metadata item for the volume."""
        put_body = json.dumps({'meta': meta_item})
        url = "volumes/%s/metadata/%s" % (volume_id, id)
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_metadata_item(self, volume_id, id):
        """Delete metadata item for the volume."""
        url = "volumes/%s/metadata/%s" % (volume_id, id)
        resp, body = self.delete(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def retype_volume(self, volume_id, **kwargs):
        """Updates volume with new volume type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#retype-a-volume
        """
        post_body = json.dumps({'os-retype': kwargs})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def force_detach_volume(self, volume_id, **kwargs):
        """Force detach a volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#force-delete-a-volume
        """
        post_body = json.dumps({'os-force_detach': kwargs})
        url = 'volumes/%s/action' % volume_id
        resp, body = self.post(url, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_volume_image_metadata(self, volume_id, **kwargs):
        """Update image metadata for the volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#set-image-metadata-for-a-volume
        """
        post_body = json.dumps({'os-set_image_metadata': {'metadata': kwargs}})
        url = "volumes/%s/action" % (volume_id)
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_image_metadata(self, volume_id, key_name):
        """Delete image metadata item for the volume."""
        post_body = json.dumps({'os-unset_image_metadata': {'key': key_name}})
        url = "volumes/%s/action" % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume_image_metadata(self, volume_id):
        """Show image metadata for the volume."""
        post_body = json.dumps({'os-show_image_metadata': {}})
        url = "volumes/%s/action" % volume_id
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def unmanage_volume(self, volume_id):
        """Unmanage volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#unmanage-a-volume
        """
        post_body = json.dumps({'os-unmanage': {}})
        resp, body = self.post('volumes/%s/action' % volume_id, post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)
