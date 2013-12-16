# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 IBM Corp.
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
import urllib

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest import exceptions
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_11


class VolumesClientXML(RestClientXML):
    """
    Client class to send CRUD Volume API requests to a Cinder endpoint
    """

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(VolumesClientXML, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.volume.catalog_type
        self.build_interval = self.config.compute.build_interval
        self.build_timeout = self.config.compute.build_timeout

    def _parse_volume(self, body):
        vol = dict((attr, body.get(attr)) for attr in body.keys())

        for child in body.getchildren():
            tag = child.tag
            if tag.startswith("{"):
                ns, tag = tag.split("}", 1)
            if tag == 'metadata':
                vol['metadata'] = dict((meta.get('key'),
                                       meta.text) for meta in
                                       child.getchildren())
            else:
                vol[tag] = xml_to_json(child)
        return vol

    def get_attachment_from_volume(self, volume):
        """Return the element 'attachment' from input volumes."""
        return volume['attachments']['attachment']

    def _check_if_bootable(self, volume):
        """
        Check if the volume is bootable, also change the value
        of 'bootable' from string to boolean.
        """

        # NOTE(jdg): Version 1 of Cinder API uses lc strings
        # We should consider being explicit in this check to
        # avoid introducing bugs like: LP #1227837

        if volume['bootable'].lower() == 'true':
            volume['bootable'] = True
        elif volume['bootable'].lower() == 'false':
            volume['bootable'] = False
        else:
            raise ValueError(
                'bootable flag is supposed to be either True or False,'
                'it is %s' % volume['bootable'])
        return volume

    def list_volumes(self, params=None):
        """List all the volumes created."""
        url = 'volumes'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        volumes = []
        if body is not None:
            volumes += [self._parse_volume(vol) for vol in list(body)]
        for v in volumes:
            v = self._check_if_bootable(v)
        return resp, volumes

    def list_volumes_with_detail(self, params=None):
        """List all the details of volumes."""
        url = 'volumes/detail'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        volumes = []
        if body is not None:
            volumes += [self._parse_volume(vol) for vol in list(body)]
        for v in volumes:
            v = self._check_if_bootable(v)
        return resp, volumes

    def get_volume(self, volume_id):
        """Returns the details of a single volume."""
        url = "volumes/%s" % str(volume_id)
        resp, body = self.get(url, self.headers)
        body = self._parse_volume(etree.fromstring(body))
        body = self._check_if_bootable(body)
        return resp, body

    def create_volume(self, size, **kwargs):
        """Creates a new Volume.

        :param size: Size of volume in GB. (Required)
        :param display_name: Optional Volume Name.
        :param metadata: An optional dictionary of values for metadata.
        :param volume_type: Optional Name of volume_type for the volume
        :param snapshot_id: When specified the volume is created from
                            this snapshot
        :param imageRef: When specified the volume is created from this
                         image
        """
        # NOTE(afazekas): it should use a volume namespace
        volume = Element("volume", xmlns=XMLNS_11, size=size)

        if 'metadata' in kwargs:
            _metadata = Element('metadata')
            volume.append(_metadata)
            for key, value in kwargs['metadata'].items():
                meta = Element('meta')
                meta.add_attr('key', key)
                meta.append(Text(value))
                _metadata.append(meta)
            attr_to_add = kwargs.copy()
            del attr_to_add['metadata']
        else:
            attr_to_add = kwargs

        for key, value in attr_to_add.items():
            volume.add_attr(key, value)

        resp, body = self.post('volumes', str(Document(volume)),
                               self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def update_volume(self, volume_id, **kwargs):
        """Updates the Specified Volume."""
        put_body = Element("volume", xmlns=XMLNS_11, **kwargs)

        resp, body = self.put('volumes/%s' % volume_id,
                              str(Document(put_body)),
                              self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume."""
        return self.delete("volumes/%s" % str(volume_id))

    def wait_for_volume_status(self, volume_id, status):
        """Waits for a Volume to reach a given status."""
        resp, body = self.get_volume(volume_id)
        volume_status = body['status']
        start = int(time.time())

        while volume_status != status:
            time.sleep(self.build_interval)
            resp, body = self.get_volume(volume_id)
            volume_status = body['status']
            if volume_status == 'error':
                raise exceptions.VolumeBuildErrorException(volume_id=volume_id)

            if int(time.time()) - start >= self.build_timeout:
                message = 'Volume %s failed to reach %s status within '\
                          'the required time (%s s).' % (volume_id,
                                                         status,
                                                         self.build_timeout)
                raise exceptions.TimeoutException(message)

    def is_resource_deleted(self, id):
        try:
            self.get_volume(id)
        except exceptions.NotFound:
            return True
        return False

    def attach_volume(self, volume_id, instance_uuid, mountpoint):
        """Attaches a volume to a given instance on a given mountpoint."""
        post_body = Element("os-attach",
                            instance_uuid=instance_uuid,
                            mountpoint=mountpoint
                            )
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def detach_volume(self, volume_id):
        """Detaches a volume from an instance."""
        post_body = Element("os-detach")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def upload_volume(self, volume_id, image_name, disk_format):
        """Uploads a volume in Glance."""
        post_body = Element("os-volume_upload_image",
                            image_name=image_name,
                            disk_format=disk_format)
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        volume = xml_to_json(etree.fromstring(body))
        return resp, volume

    def extend_volume(self, volume_id, extend_size):
        """Extend a volume."""
        post_body = Element("os-extend",
                            new_size=extend_size)
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def reset_volume_status(self, volume_id, status):
        """Reset the Specified Volume's Status."""
        post_body = Element("os-reset_status",
                            status=status
                            )
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def volume_begin_detaching(self, volume_id):
        """Volume Begin Detaching."""
        post_body = Element("os-begin_detaching")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def volume_roll_detaching(self, volume_id):
        """Volume Roll Detaching."""
        post_body = Element("os-roll_detaching")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def reserve_volume(self, volume_id):
        """Reserves a volume."""
        post_body = Element("os-reserve")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def unreserve_volume(self, volume_id):
        """Restore a reserved volume ."""
        post_body = Element("os-unreserve")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def create_volume_transfer(self, vol_id, display_name=None):
        """Create a volume transfer."""
        post_body = Element("transfer",
                            volume_id=vol_id)
        if display_name:
            post_body.add_attr('name', display_name)
        resp, body = self.post('os-volume-transfer',
                               str(Document(post_body)),
                               self.headers)
        volume = xml_to_json(etree.fromstring(body))
        return resp, volume

    def get_volume_transfer(self, transfer_id):
        """Returns the details of a volume transfer."""
        url = "os-volume-transfer/%s" % str(transfer_id)
        resp, body = self.get(url, self.headers)
        volume = xml_to_json(etree.fromstring(body))
        return resp, volume

    def list_volume_transfers(self, params=None):
        """List all the volume transfers created."""
        url = 'os-volume-transfer'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        volumes = []
        if body is not None:
            volumes += [self._parse_volume_transfer(vol) for vol in list(body)]
        return resp, volumes

    def _parse_volume_transfer(self, body):
        vol = dict((attr, body.get(attr)) for attr in body.keys())
        for child in body.getchildren():
            tag = child.tag
            if tag.startswith("{"):
                tag = tag.split("}", 1)
            vol[tag] = xml_to_json(child)
        return vol

    def delete_volume_transfer(self, transfer_id):
        """Delete a volume transfer."""
        return self.delete("os-volume-transfer/%s" % str(transfer_id))

    def accept_volume_transfer(self, transfer_id, transfer_auth_key):
        """Accept a volume transfer."""
        post_body = Element("accept", auth_key=transfer_auth_key)
        url = 'os-volume-transfer/%s/accept' % transfer_id
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        volume = xml_to_json(etree.fromstring(body))
        return resp, volume

    def update_volume_readonly(self, volume_id, readonly):
        """Update the Specified Volume readonly."""
        post_body = Element("os-update_readonly_flag",
                            readonly=readonly)
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def force_delete_volume(self, volume_id):
        """Force Delete Volume."""
        post_body = Element("os-force_delete")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(Document(post_body)), self.headers)
        if body:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def _metadata_body(self, meta):
        post_body = Element('metadata')
        for k, v in meta.items():
            data = Element('meta', key=k)
            data.append(Text(v))
            post_body.append(data)
        return post_body

    def _parse_key_value(self, node):
        """Parse <foo key='key'>value</foo> data into {'key': 'value'}."""
        data = {}
        for node in node.getchildren():
            data[node.get('key')] = node.text
        return data

    def create_volume_metadata(self, volume_id, metadata):
        """Create metadata for the volume."""
        post_body = self._metadata_body(metadata)
        resp, body = self.post('volumes/%s/metadata' % volume_id,
                               str(Document(post_body)),
                               self.headers)
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def get_volume_metadata(self, volume_id):
        """Get metadata of the volume."""
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.get(url, self.headers)
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def update_volume_metadata(self, volume_id, metadata):
        """Update metadata for the volume."""
        put_body = self._metadata_body(metadata)
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.put(url, str(Document(put_body)), self.headers)
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def update_volume_metadata_item(self, volume_id, id, meta_item):
        """Update metadata item for the volume."""
        for k, v in meta_item.items():
            put_body = Element('meta', key=k)
            put_body.append(Text(v))
        url = "volumes/%s/metadata/%s" % (str(volume_id), str(id))
        resp, body = self.put(url, str(Document(put_body)), self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_volume_metadata_item(self, volume_id, id):
        """Delete metadata item for the volume."""
        url = "volumes/%s/metadata/%s" % (str(volume_id), str(id))
        return self.delete(url)
