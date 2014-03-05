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
from xml.sax import saxutils

from tempest.common import rest_client
from tempest import config
from tempest import exceptions
from tempest.services.compute.xml import common

CONF = config.CONF

VOLUME_NS_BASE = 'http://docs.openstack.org/volume/ext/'
VOLUME_HOST_NS = VOLUME_NS_BASE + 'volume_host_attribute/api/v1'
VOLUME_MIG_STATUS_NS = VOLUME_NS_BASE + 'volume_mig_status_attribute/api/v1'
VOLUMES_TENANT_NS = VOLUME_NS_BASE + 'volume_tenant_attribute/api/v1'


class VolumesClientXML(rest_client.RestClient):
    """
    Client class to send CRUD Volume API requests to a Cinder endpoint
    """
    TYPE = "xml"

    def __init__(self, auth_provider):
        super(VolumesClientXML, self).__init__(auth_provider)
        self.service = CONF.volume.catalog_type
        self.build_interval = CONF.compute.build_interval
        self.build_timeout = CONF.compute.build_timeout

    def _translate_attributes_to_json(self, volume):
        volume_host_attr = '{' + VOLUME_HOST_NS + '}host'
        volume_mig_stat_attr = '{' + VOLUME_MIG_STATUS_NS + '}migstat'
        volume_mig_name_attr = '{' + VOLUME_MIG_STATUS_NS + '}name_id'
        volume_tenant_id_attr = '{' + VOLUMES_TENANT_NS + '}tenant_id'
        if volume_host_attr in volume:
            volume['os-vol-host-attr:host'] = volume.pop(volume_host_attr)
        if volume_mig_stat_attr in volume:
            volume['os-vol-mig-status-attr:migstat'] = volume.pop(
                volume_mig_stat_attr)
        if volume_mig_name_attr in volume:
            volume['os-vol-mig-status-attr:name_id'] = volume.pop(
                volume_mig_name_attr)
        if volume_tenant_id_attr in volume:
            volume['os-vol-tenant-attr:tenant_id'] = volume.pop(
                volume_tenant_id_attr)

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
                vol[tag] = common.xml_to_json(child)
        self._translate_attributes_to_json(vol)
        self._check_if_bootable(vol)
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

        resp, body = self.get(url)
        body = etree.fromstring(body)
        volumes = []
        if body is not None:
            volumes += [self._parse_volume(vol) for vol in list(body)]
        return resp, volumes

    def list_volumes_with_detail(self, params=None):
        """List all the details of volumes."""
        url = 'volumes/detail'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = etree.fromstring(body)
        volumes = []
        if body is not None:
            volumes += [self._parse_volume(vol) for vol in list(body)]
        return resp, volumes

    def get_volume(self, volume_id):
        """Returns the details of a single volume."""
        url = "volumes/%s" % str(volume_id)
        resp, body = self.get(url)
        body = self._parse_volume(etree.fromstring(body))
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
        volume = common.Element("volume", xmlns=common.XMLNS_11, size=size)

        if 'metadata' in kwargs:
            _metadata = common.Element('metadata')
            volume.append(_metadata)
            for key, value in kwargs['metadata'].items():
                meta = common.Element('meta')
                meta.add_attr('key', key)
                meta.append(common.Text(value))
                _metadata.append(meta)
            attr_to_add = kwargs.copy()
            del attr_to_add['metadata']
        else:
            attr_to_add = kwargs

        for key, value in attr_to_add.items():
            volume.add_attr(key, value)

        resp, body = self.post('volumes', str(common.Document(volume)))
        body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def update_volume(self, volume_id, **kwargs):
        """Updates the Specified Volume."""
        put_body = common.Element("volume", xmlns=common.XMLNS_11, **kwargs)

        resp, body = self.put('volumes/%s' % volume_id,
                              str(common.Document(put_body)))
        body = common.xml_to_json(etree.fromstring(body))
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
        post_body = common.Element("os-attach",
                                   instance_uuid=instance_uuid,
                                   mountpoint=mountpoint
                                   )
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def detach_volume(self, volume_id):
        """Detaches a volume from an instance."""
        post_body = common.Element("os-detach")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def upload_volume(self, volume_id, image_name, disk_format):
        """Uploads a volume in Glance."""
        post_body = common.Element("os-volume_upload_image",
                                   image_name=image_name,
                                   disk_format=disk_format)
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        volume = common.xml_to_json(etree.fromstring(body))
        return resp, volume

    def extend_volume(self, volume_id, extend_size):
        """Extend a volume."""
        post_body = common.Element("os-extend",
                                   new_size=extend_size)
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def reset_volume_status(self, volume_id, status):
        """Reset the Specified Volume's Status."""
        post_body = common.Element("os-reset_status",
                                   status=status
                                   )
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def volume_begin_detaching(self, volume_id):
        """Volume Begin Detaching."""
        post_body = common.Element("os-begin_detaching")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def volume_roll_detaching(self, volume_id):
        """Volume Roll Detaching."""
        post_body = common.Element("os-roll_detaching")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def reserve_volume(self, volume_id):
        """Reserves a volume."""
        post_body = common.Element("os-reserve")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def unreserve_volume(self, volume_id):
        """Restore a reserved volume ."""
        post_body = common.Element("os-unreserve")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def create_volume_transfer(self, vol_id, display_name=None):
        """Create a volume transfer."""
        post_body = common.Element("transfer",
                                   volume_id=vol_id)
        if display_name:
            post_body.add_attr('name', display_name)
        resp, body = self.post('os-volume-transfer',
                               str(common.Document(post_body)))
        volume = common.xml_to_json(etree.fromstring(body))
        return resp, volume

    def get_volume_transfer(self, transfer_id):
        """Returns the details of a volume transfer."""
        url = "os-volume-transfer/%s" % str(transfer_id)
        resp, body = self.get(url)
        volume = common.xml_to_json(etree.fromstring(body))
        return resp, volume

    def list_volume_transfers(self, params=None):
        """List all the volume transfers created."""
        url = 'os-volume-transfer'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
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
            vol[tag] = common.xml_to_json(child)
        return vol

    def delete_volume_transfer(self, transfer_id):
        """Delete a volume transfer."""
        return self.delete("os-volume-transfer/%s" % str(transfer_id))

    def accept_volume_transfer(self, transfer_id, transfer_auth_key):
        """Accept a volume transfer."""
        post_body = common.Element("accept", auth_key=transfer_auth_key)
        url = 'os-volume-transfer/%s/accept' % transfer_id
        resp, body = self.post(url, str(common.Document(post_body)))
        volume = common.xml_to_json(etree.fromstring(body))
        return resp, volume

    def update_volume_readonly(self, volume_id, readonly):
        """Update the Specified Volume readonly."""
        post_body = common.Element("os-update_readonly_flag",
                                   readonly=readonly)
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def force_delete_volume(self, volume_id):
        """Force Delete Volume."""
        post_body = common.Element("os-force_delete")
        url = 'volumes/%s/action' % str(volume_id)
        resp, body = self.post(url, str(common.Document(post_body)))
        if body:
            body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def _metadata_body(self, meta):
        post_body = common.Element('metadata')
        for k, v in meta.items():
            data = common.Element('meta', key=k)
            # Escape value to allow for special XML chars
            data.append(common.Text(saxutils.escape(v)))
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
                               str(common.Document(post_body)))
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def get_volume_metadata(self, volume_id):
        """Get metadata of the volume."""
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.get(url)
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def update_volume_metadata(self, volume_id, metadata):
        """Update metadata for the volume."""
        put_body = self._metadata_body(metadata)
        url = "volumes/%s/metadata" % str(volume_id)
        resp, body = self.put(url, str(common.Document(put_body)))
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def update_volume_metadata_item(self, volume_id, id, meta_item):
        """Update metadata item for the volume."""
        for k, v in meta_item.items():
            put_body = common.Element('meta', key=k)
            put_body.append(common.Text(v))
        url = "volumes/%s/metadata/%s" % (str(volume_id), str(id))
        resp, body = self.put(url, str(common.Document(put_body)))
        body = common.xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_volume_metadata_item(self, volume_id, id):
        """Delete metadata item for the volume."""
        url = "volumes/%s/metadata/%s" % (str(volume_id), str(id))
        return self.delete(url)
