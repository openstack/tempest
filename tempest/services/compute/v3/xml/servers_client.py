# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 IBM Corp.
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from tempest.common import waiters
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import Text
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_V3


LOG = logging.getLogger(__name__)


def _translate_ip_xml_json(ip):
    """
    Convert the address version to int.
    """
    ip = dict(ip)
    version = ip.get('version')
    if version:
        ip['version'] = int(version)
    if ip.get('type'):
        ip['type'] = ip.get('type')
    if ip.get('mac_addr'):
        ip['mac_addr'] = ip.get('mac_addr')
    return ip


def _translate_network_xml_to_json(network):
    return [_translate_ip_xml_json(ip.attrib)
            for ip in network.findall('{%s}ip' % XMLNS_V3)]


def _translate_addresses_xml_to_json(xml_addresses):
    return dict((network.attrib['id'], _translate_network_xml_to_json(network))
                for network in xml_addresses.findall('{%s}network' % XMLNS_V3))


def _translate_server_xml_to_json(xml_dom):
    """Convert server XML to server JSON.

    The addresses collection does not convert well by the dumb xml_to_json.
    This method does some pre and post-processing to deal with that.

    Translate XML addresses subtree to JSON.

    Having xml_doc similar to
    <api:server  xmlns:api="http://docs.openstack.org/compute/api/v3">
        <api:addresses>
            <api:network id="foo_novanetwork">
                <api:ip version="4" addr="192.168.0.4"/>
            </api:network>
            <api:network id="bar_novanetwork">
                <api:ip version="4" addr="10.1.0.4"/>
                <api:ip version="6" addr="2001:0:0:1:2:3:4:5"/>
            </api:network>
        </api:addresses>
    </api:server>

    the _translate_server_xml_to_json(etree.fromstring(xml_doc)) should produce
    something like

    {'addresses': {'bar_novanetwork': [{'addr': '10.1.0.4', 'version': 4},
                                       {'addr': '2001:0:0:1:2:3:4:5',
                                        'version': 6}],
                   'foo_novanetwork': [{'addr': '192.168.0.4', 'version': 4}]}}
    """
    nsmap = {'api': XMLNS_V3}
    addresses = xml_dom.xpath('/api:server/api:addresses', namespaces=nsmap)
    if addresses:
        if len(addresses) > 1:
            raise ValueError('Expected only single `addresses` element.')
        json_addresses = _translate_addresses_xml_to_json(addresses[0])
        json = xml_to_json(xml_dom)
        json['addresses'] = json_addresses
    else:
        json = xml_to_json(xml_dom)
    disk_config = ('{http://docs.openstack.org'
                   '/compute/ext/disk_config/api/v3}disk_config')
    terminated_at = ('{http://docs.openstack.org/'
                     'compute/ext/os-server-usage/api/v3}terminated_at')
    launched_at = ('{http://docs.openstack.org'
                   '/compute/ext/os-server-usage/api/v3}launched_at')
    power_state = ('{http://docs.openstack.org'
                   '/compute/ext/extended_status/api/v3}power_state')
    availability_zone = ('{http://docs.openstack.org'
                         '/compute/ext/extended_availability_zone/api/v3}'
                         'availability_zone')
    vm_state = ('{http://docs.openstack.org'
                '/compute/ext/extended_status/api/v3}vm_state')
    task_state = ('{http://docs.openstack.org'
                  '/compute/ext/extended_status/api/v3}task_state')
    if disk_config in json:
        json['os-disk-config:disk_config'] = json.pop(disk_config)
    if terminated_at in json:
        json['os-server-usage:terminated_at'] = json.pop(terminated_at)
    if launched_at in json:
        json['os-server-usage:launched_at'] = json.pop(launched_at)
    if power_state in json:
        json['os-extended-status:power_state'] = json.pop(power_state)
    if availability_zone in json:
        json['os-extended-availability-zone:availability_zone'] = json.pop(
            availability_zone)
    if vm_state in json:
        json['os-extended-status:vm_state'] = json.pop(vm_state)
    if task_state in json:
        json['os-extended-status:task_state'] = json.pop(task_state)
    return json


class ServersV3ClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url,
                 tenant_name=None, auth_version='v2'):
        super(ServersV3ClientXML, self).__init__(config, username, password,
                                                 auth_url, tenant_name,
                                                 auth_version=auth_version)
        self.service = self.config.compute.catalog_v3_type

    def _parse_key_value(self, node):
        """Parse <foo key='key'>value</foo> data into {'key': 'value'}."""
        data = {}
        for node in node.getchildren():
            data[node.get('key')] = node.text
        return data

    def _parse_links(self, node, json):
        del json['link']
        json['links'] = []
        for linknode in node.findall('{http://www.w3.org/2005/Atom}link'):
            json['links'].append(xml_to_json(linknode))

    def _parse_server(self, body):
        json = _translate_server_xml_to_json(body)

        if 'metadata' in json and json['metadata']:
            # NOTE(danms): if there was metadata, we need to re-parse
            # that as a special type
            metadata_tag = body.find('{%s}metadata' % XMLNS_V3)
            json["metadata"] = self._parse_key_value(metadata_tag)
        if 'link' in json:
            self._parse_links(body, json)
        for sub in ['image', 'flavor']:
            if sub in json and 'link' in json[sub]:
                self._parse_links(body, json[sub])
        return json

    def _parse_xml_virtual_interfaces(self, xml_dom):
        """
        Return server's virtual interfaces XML as JSON.
        """
        data = {"virtual_interfaces": []}
        for iface in xml_dom.getchildren():
            data["virtual_interfaces"].append(
                {"id": iface.get("id"),
                 "mac_address": iface.get("mac_address")})
        return data

    def get_server(self, server_id):
        """Returns the details of an existing server."""
        resp, body = self.get("servers/%s" % str(server_id), self.headers)
        server = self._parse_server(etree.fromstring(body))
        return resp, server

    def lock_server(self, server_id, **kwargs):
        """Locks the given server."""
        return self.action(server_id, 'lock', None, **kwargs)

    def unlock_server(self, server_id, **kwargs):
        """Unlocks the given server."""
        return self.action(server_id, 'unlock', None, **kwargs)

    def suspend_server(self, server_id, **kwargs):
        """Suspends the provided server."""
        return self.action(server_id, 'suspend', None, **kwargs)

    def resume_server(self, server_id, **kwargs):
        """Un-suspends the provided server."""
        return self.action(server_id, 'resume', None, **kwargs)

    def pause_server(self, server_id, **kwargs):
        """Pauses the provided server."""
        return self.action(server_id, 'pause', None, **kwargs)

    def unpause_server(self, server_id, **kwargs):
        """Un-pauses the provided server."""
        return self.action(server_id, 'unpause', None, **kwargs)

    def reset_state(self, server_id, state='error'):
        """Resets the state of a server to active/error."""
        return self.action(server_id, 'reset_state', None, state=state)

    def delete_server(self, server_id):
        """Deletes the given server."""
        return self.delete("servers/%s" % str(server_id))

    def _parse_array(self, node):
        array = []
        for child in node.getchildren():
            array.append(xml_to_json(child))
        return array

    def list_servers(self, params=None):
        url = 'servers'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        servers = self._parse_array(etree.fromstring(body))
        return resp, {"servers": servers}

    def list_servers_with_detail(self, params=None):
        url = 'servers/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url, self.headers)
        servers = self._parse_array(etree.fromstring(body))
        return resp, {"servers": servers}

    def update_server(self, server_id, name=None, meta=None, access_ip_v4=None,
                      access_ip_v6=None, disk_config=None):
        doc = Document()
        server = Element("server")
        doc.append(server)

        if name is not None:
            server.add_attr("name", name)
        if access_ip_v4 is not None:
            server.add_attr("access_ip_v4", access_ip_v4)
        if access_ip_v6 is not None:
            server.add_attr("access_ip_v6", access_ip_v6)
        if meta is not None:
            metadata = Element("metadata")
            server.append(metadata)
            for k, v in meta:
                meta = Element("meta", key=k)
                meta.append(Text(v))
                metadata.append(meta)

        resp, body = self.put('servers/%s' % str(server_id),
                              str(doc), self.headers)
        return resp, xml_to_json(etree.fromstring(body))

    def create_server(self, name, image_ref, flavor_ref, **kwargs):
        """
        Creates an instance of a server.
        name (Required): The name of the server.
        image_ref (Required): Reference to the image used to build the server.
        flavor_ref (Required): The flavor used to build the server.
        Following optional keyword arguments are accepted:
        admin_password: Sets the initial root password.
        key_name: Key name of keypair that was created earlier.
        meta: A dictionary of values to be used as metadata.
        personality: A list of dictionaries for files to be injected into
        the server.
        security_groups: A list of security group dicts.
        networks: A list of network dicts with UUID and fixed_ip.
        user_data: User data for instance.
        availability_zone: Availability zone in which to launch instance.
        access_ip_v4: The IPv4 access address for the server.
        access_ip_v6: The IPv6 access address for the server.
        min_count: Count of minimum number of instances to launch.
        max_count: Count of maximum number of instances to launch.
        disk_config: Determines if user or admin controls disk configuration.
        return_reservation_id: Enable/Disable the return of reservation id.
        """
        server = Element("server",
                         imageRef=image_ref,
                         xmlns=XMLNS_V3,
                         flavor_ref=flavor_ref,
                         image_ref=image_ref,
                         name=name)
        attrs = ["admin_pass", "access_ip_v4", "access_ip_v6", "key_name",
                 ("os-user-data:user_data",
                  'user_data',
                  'xmlns:os-user-data',
                  "http://docs.openstack.org/compute/ext/userdata/api/v3"),
                 ("os-availability-zone:availability_zone",
                  'availability_zone',
                  'xmlns:os-availability-zone',
                  "http://docs.openstack.org/compute/ext/"
                  "availabilityzone/api/v3"),
                 ("os-multiple-create:min_count",
                  'min_count',
                  'xmlns:os-multiple-create',
                  "http://docs.openstack.org/compute/ext/"
                  "multiplecreate/api/v3"),
                 ("os-multiple-create:max_count",
                  'max_count',
                  'xmlns:os-multiple-create',
                  "http://docs.openstack.org/compute/ext/"
                  "multiplecreate/api/v3"),
                 ("os-multiple-create:return_reservation_id",
                  "return_reservation_id",
                  'xmlns:os-multiple-create',
                  "http://docs.openstack.org/compute/ext/"
                  "multiplecreate/api/v3"),
                 ("os-disk-config:disk_config",
                  "disk_config",
                  "xmlns:os-disk-config",
                  "http://docs.openstack.org/"
                  "compute/ext/disk_config/api/v3")]

        for attr in attrs:
            if isinstance(attr, tuple):
                post_param = attr[0]
                key = attr[1]
                value = kwargs.get(key)
                if value is not None:
                    server.add_attr(attr[2], attr[3])
                    server.add_attr(post_param, value)
            else:
                post_param = attr
                key = attr
                value = kwargs.get(key)
                if value is not None:
                    server.add_attr(post_param, value)

        if 'security_groups' in kwargs:
            secgroups = Element("security_groups")
            server.append(secgroups)
            for secgroup in kwargs['security_groups']:
                s = Element("security_group", name=secgroup['name'])
                secgroups.append(s)

        if 'networks' in kwargs:
            networks = Element("networks")
            server.append(networks)
            for network in kwargs['networks']:
                s = Element("network", uuid=network['uuid'],
                            fixed_ip=network['fixed_ip'])
                networks.append(s)

        if 'meta' in kwargs:
            metadata = Element("metadata")
            server.append(metadata)
            for k, v in kwargs['meta'].items():
                meta = Element("meta", key=k)
                meta.append(Text(v))
                metadata.append(meta)

        if 'personality' in kwargs:
            personality = Element('personality')
            server.append(personality)
            for k in kwargs['personality']:
                temp = Element('file', path=k['path'])
                temp.append(Text(k['contents']))
                personality.append(temp)

        resp, body = self.post('servers', str(Document(server)), self.headers)
        server = self._parse_server(etree.fromstring(body))
        return resp, server

    def wait_for_server_status(self, server_id, status, extra_timeout=0):
        """Waits for a server to reach a given status."""
        return waiters.wait_for_server_status(self, server_id, status,
                                              extra_timeout=extra_timeout)

    def wait_for_server_termination(self, server_id, ignore_error=False):
        """Waits for server to reach termination."""
        start_time = int(time.time())
        while True:
            try:
                resp, body = self.get_server(server_id)
            except exceptions.NotFound:
                return

            server_status = body['status']
            if server_status == 'ERROR' and not ignore_error:
                raise exceptions.BuildErrorException

            if int(time.time()) - start_time >= self.build_timeout:
                raise exceptions.TimeoutException

            time.sleep(self.build_interval)

    def _parse_network(self, node):
        addrs = []
        for child in node.getchildren():
            addrs.append({'version': int(child.get('version')),
                         'addr': child.get('addr')})
        return {node.get('id'): addrs}

    def list_addresses(self, server_id):
        """Lists all addresses for a server."""
        resp, body = self.get("servers/%s/ips" % str(server_id), self.headers)

        networks = {}
        xml_list = etree.fromstring(body)
        for child in xml_list.getchildren():
            network = self._parse_network(child)
            networks.update(**network)

        return resp, networks

    def list_addresses_by_network(self, server_id, network_id):
        """Lists all addresses of a specific network type for a server."""
        resp, body = self.get("servers/%s/ips/%s" % (str(server_id),
                                                     network_id),
                              self.headers)
        network = self._parse_network(etree.fromstring(body))

        return resp, network

    def action(self, server_id, action_name, response_key, **kwargs):
        if 'xmlns' not in kwargs:
            kwargs['xmlns'] = XMLNS_V3
        doc = Document((Element(action_name, **kwargs)))
        resp, body = self.post("servers/%s/action" % server_id,
                               str(doc), self.headers)
        if response_key is not None:
            body = xml_to_json(etree.fromstring(body))
        return resp, body

    def change_password(self, server_id, password):
        return self.action(server_id, "change_password", None,
                           admin_pass=password)

    def reboot(self, server_id, reboot_type):
        return self.action(server_id, "reboot", None, type=reboot_type)

    def rebuild(self, server_id, image_ref, **kwargs):
        kwargs['image_ref'] = image_ref
        if 'disk_config' in kwargs:
            kwargs['os-disk-config:disk_config'] = kwargs['disk_config']
            del kwargs['disk_config']
            kwargs['xmlns:os-disk-config'] = "http://docs.openstack.org/"\
                                             "compute/ext/disk_config/api/v3"
            kwargs['xmlns:atom'] = "http://www.w3.org/2005/Atom"
        if 'xmlns' not in kwargs:
            kwargs['xmlns'] = XMLNS_V3

        attrs = kwargs.copy()
        if 'metadata' in attrs:
            del attrs['metadata']
        rebuild = Element("rebuild",
                          **attrs)

        if 'metadata' in kwargs:
            metadata = Element("metadata")
            rebuild.append(metadata)
            for k, v in kwargs['metadata'].items():
                meta = Element("meta", key=k)
                meta.append(Text(v))
                metadata.append(meta)

        resp, body = self.post('servers/%s/action' % server_id,
                               str(Document(rebuild)), self.headers)
        server = self._parse_server(etree.fromstring(body))
        return resp, server

    def resize(self, server_id, flavor_ref, **kwargs):
        if 'disk_config' in kwargs:
            kwargs['os-disk-config:disk_config'] = kwargs['disk_config']
            del kwargs['disk_config']
            kwargs['xmlns:os-disk-config'] = "http://docs.openstack.org/"\
                                             "compute/ext/disk_config/api/v3"
            kwargs['xmlns:atom'] = "http://www.w3.org/2005/Atom"
        kwargs['flavor_ref'] = flavor_ref
        return self.action(server_id, 'resize', None, **kwargs)

    def confirm_resize(self, server_id, **kwargs):
        return self.action(server_id, 'confirm_resize', None, **kwargs)

    def revert_resize(self, server_id, **kwargs):
        return self.action(server_id, 'revert_resize', None, **kwargs)

    def stop(self, server_id, **kwargs):
        return self.action(server_id, 'stop', None, **kwargs)

    def start(self, server_id, **kwargs):
        return self.action(server_id, 'start', None, **kwargs)

    def create_image(self, server_id, name, meta=None):
        """Creates an image of the original server."""
        post_body = Element('create_image', name=name)

        if meta:
            metadata = Element('metadata')
            post_body.append(metadata)
            for k, v in meta.items():
                data = Element('meta', key=k)
                data.append(Text(v))
                metadata.append(data)
        resp, body = self.post('servers/%s/action' % str(server_id),
                               str(Document(post_body)), self.headers)
        return resp, body

    def add_security_group(self, server_id, name):
        return self.action(server_id, 'add_security_group', None, name=name)

    def remove_security_group(self, server_id, name):
        return self.action(server_id, 'remove_security_group', None, name=name)

    def live_migrate_server(self, server_id, dest_host, use_block_migration):
        """This should be called with administrator privileges ."""

        req_body = Element("migrate_live",
                           xmlns=XMLNS_V3,
                           disk_over_commit=False,
                           block_migration=use_block_migration,
                           host=dest_host)

        resp, body = self.post("servers/%s/action" % str(server_id),
                               str(Document(req_body)), self.headers)
        return resp, body

    def list_server_metadata(self, server_id):
        resp, body = self.get("servers/%s/metadata" % str(server_id),
                              self.headers)
        body = self._parse_key_value(etree.fromstring(body))
        return resp, body

    def set_server_metadata(self, server_id, meta, no_metadata_field=False):
        doc = Document()
        if not no_metadata_field:
            metadata = Element("metadata")
            doc.append(metadata)
            for k, v in meta.items():
                meta_element = Element("meta", key=k)
                meta_element.append(Text(v))
                metadata.append(meta_element)
        resp, body = self.put('servers/%s/metadata' % str(server_id),
                              str(doc), self.headers)
        return resp, xml_to_json(etree.fromstring(body))

    def update_server_metadata(self, server_id, meta):
        doc = Document()
        metadata = Element("metadata")
        doc.append(metadata)
        for k, v in meta.items():
            meta_element = Element("meta", key=k)
            meta_element.append(Text(v))
            metadata.append(meta_element)
        resp, body = self.post("/servers/%s/metadata" % str(server_id),
                               str(doc), headers=self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def get_server_metadata_item(self, server_id, key):
        resp, body = self.get("servers/%s/metadata/%s" % (str(server_id), key),
                              headers=self.headers)
        return resp, dict([(etree.fromstring(body).attrib['key'],
                            xml_to_json(etree.fromstring(body)))])

    def set_server_metadata_item(self, server_id, key, meta):
        doc = Document()
        for k, v in meta.items():
            meta_element = Element("meta", key=k)
            meta_element.append(Text(v))
            doc.append(meta_element)
        resp, body = self.put('servers/%s/metadata/%s' % (str(server_id), key),
                              str(doc), self.headers)
        return resp, xml_to_json(etree.fromstring(body))

    def delete_server_metadata_item(self, server_id, key):
        resp, body = self.delete("servers/%s/metadata/%s" %
                                 (str(server_id), key))
        return resp, body

    def get_console_output(self, server_id, length):
        return self.action(server_id, 'get_console_output', 'output',
                           length=length)

    def rescue_server(self, server_id, admin_pass=None):
        """Rescue the provided server."""
        return self.action(server_id, 'rescue', None, admin_pass=admin_pass)

    def unrescue_server(self, server_id):
        """Unrescue the provided server."""
        return self.action(server_id, 'unrescue', None)

    def attach_volume(self, server_id, volume_id, device='/dev/vdz'):
        return self.action(server_id, "attach", None, volume_id=volume_id,
                           device=device)

    def detach_volume(self, server_id, volume_id):
        return self.action(server_id, "detach", None, volume_id=volume_id)

    def get_server_diagnostics(self, server_id):
        """Get the usage data for a server."""
        resp, body = self.get("servers/%s/os-server-diagnostics" % server_id,
                              self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def list_instance_actions(self, server_id):
        """List the provided server action."""
        resp, body = self.get("servers/%s/os-instance-actions" % server_id,
                              self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, body

    def get_instance_action(self, server_id, request_id):
        """Returns the action details of the provided server."""
        resp, body = self.get("servers/%s/os-instance-actions/%s" %
                              (server_id, request_id), self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body
