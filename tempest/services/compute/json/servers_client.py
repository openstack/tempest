# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

import json
import time
import urllib

from tempest.common.rest_client import RestClient
from tempest.common import waiters
from tempest import exceptions


class ServersClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None,
                 auth_version='v2'):
        super(ServersClientJSON, self).__init__(config, username, password,
                                                auth_url, tenant_name,
                                                auth_version=auth_version)
        self.service = self.config.compute.catalog_type

    def create_server(self, name, image_ref, flavor_ref, **kwargs):
        """
        Creates an instance of a server.
        name (Required): The name of the server.
        image_ref (Required): Reference to the image used to build the server.
        flavor_ref (Required): The flavor used to build the server.
        Following optional keyword arguments are accepted:
        adminPass: Sets the initial root password.
        key_name: Key name of keypair that was created earlier.
        meta: A dictionary of values to be used as metadata.
        personality: A list of dictionaries for files to be injected into
        the server.
        security_groups: A list of security group dicts.
        networks: A list of network dicts with UUID and fixed_ip.
        user_data: User data for instance.
        availability_zone: Availability zone in which to launch instance.
        accessIPv4: The IPv4 access address for the server.
        accessIPv6: The IPv6 access address for the server.
        min_count: Count of minimum number of instances to launch.
        max_count: Count of maximum number of instances to launch.
        disk_config: Determines if user or admin controls disk configuration.
        return_reservation_id: Enable/Disable the return of reservation id
        """
        post_body = {
            'name': name,
            'imageRef': image_ref,
            'flavorRef': flavor_ref
        }

        for option in ['personality', 'adminPass', 'key_name',
                       'security_groups', 'networks', 'user_data',
                       'availability_zone', 'accessIPv4', 'accessIPv6',
                       'min_count', 'max_count', ('metadata', 'meta'),
                       ('OS-DCF:diskConfig', 'disk_config'),
                       'return_reservation_id']:
            if isinstance(option, tuple):
                post_param = option[0]
                key = option[1]
            else:
                post_param = option
                key = option
            value = kwargs.get(key)
            if value is not None:
                post_body[post_param] = value
        post_body = json.dumps({'server': post_body})
        resp, body = self.post('servers', post_body, self.headers)

        body = json.loads(body)
        # NOTE(maurosr): this deals with the case of multiple server create
        # with return reservation id set True
        if 'reservation_id' in body:
            return resp, body
        return resp, body['server']

    def update_server(self, server_id, name=None, meta=None, accessIPv4=None,
                      accessIPv6=None):
        """
        Updates the properties of an existing server.
        server_id: The id of an existing server.
        name: The name of the server.
        personality: A list of files to be injected into the server.
        accessIPv4: The IPv4 access address for the server.
        accessIPv6: The IPv6 access address for the server.
        """

        post_body = {}

        if meta is not None:
            post_body['metadata'] = meta

        if name is not None:
            post_body['name'] = name

        if accessIPv4 is not None:
            post_body['accessIPv4'] = accessIPv4

        if accessIPv6 is not None:
            post_body['accessIPv6'] = accessIPv6

        post_body = json.dumps({'server': post_body})
        resp, body = self.put("servers/%s" % str(server_id),
                              post_body, self.headers)
        body = json.loads(body)
        return resp, body['server']

    def get_server(self, server_id):
        """Returns the details of an existing server."""
        resp, body = self.get("servers/%s" % str(server_id))
        body = json.loads(body)
        return resp, body['server']

    def delete_server(self, server_id):
        """Deletes the given server."""
        return self.delete("servers/%s" % str(server_id))

    def list_servers(self, params=None):
        """Lists all servers for a user."""

        url = 'servers'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def list_servers_with_detail(self, params=None):
        """Lists all servers in detail for a user."""

        url = 'servers/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def wait_for_server_status(self, server_id, status):
        """Waits for a server to reach a given status."""
        return waiters.wait_for_server_status(self, server_id, status)

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
                raise exceptions.BuildErrorException(server_id=server_id)

            if int(time.time()) - start_time >= self.build_timeout:
                raise exceptions.TimeoutException

            time.sleep(self.build_interval)

    def list_addresses(self, server_id):
        """Lists all addresses for a server."""
        resp, body = self.get("servers/%s/ips" % str(server_id))
        body = json.loads(body)
        return resp, body['addresses']

    def list_addresses_by_network(self, server_id, network_id):
        """Lists all addresses of a specific network type for a server."""
        resp, body = self.get("servers/%s/ips/%s" %
                              (str(server_id), network_id))
        body = json.loads(body)
        return resp, body

    def action(self, server_id, action_name, response_key, **kwargs):
        post_body = json.dumps({action_name: kwargs})
        resp, body = self.post('servers/%s/action' % str(server_id),
                               post_body, self.headers)
        if response_key is not None:
            body = json.loads(body)[response_key]
        return resp, body

    def change_password(self, server_id, adminPass):
        """Changes the root password for the server."""
        return self.action(server_id, 'changePassword', None,
                           adminPass=adminPass)

    def reboot(self, server_id, reboot_type):
        """Reboots a server."""
        return self.action(server_id, 'reboot', None, type=reboot_type)

    def rebuild(self, server_id, image_ref, **kwargs):
        """Rebuilds a server with a new image."""
        kwargs['imageRef'] = image_ref
        if 'disk_config' in kwargs:
            kwargs['OS-DCF:diskConfig'] = kwargs['disk_config']
            del kwargs['disk_config']
        return self.action(server_id, 'rebuild', 'server', **kwargs)

    def resize(self, server_id, flavor_ref, **kwargs):
        """Changes the flavor of a server."""
        kwargs['flavorRef'] = flavor_ref
        if 'disk_config' in kwargs:
            kwargs['OS-DCF:diskConfig'] = kwargs['disk_config']
            del kwargs['disk_config']
        return self.action(server_id, 'resize', None, **kwargs)

    def confirm_resize(self, server_id, **kwargs):
        """Confirms the flavor change for a server."""
        return self.action(server_id, 'confirmResize', None, **kwargs)

    def revert_resize(self, server_id, **kwargs):
        """Reverts a server back to its original flavor."""
        return self.action(server_id, 'revertResize', None, **kwargs)

    def create_image(self, server_id, name):
        """Creates an image of the given server."""
        return self.action(server_id, 'createImage', None, name=name)

    def list_server_metadata(self, server_id):
        resp, body = self.get("servers/%s/metadata" % str(server_id))
        body = json.loads(body)
        return resp, body['metadata']

    def set_server_metadata(self, server_id, meta, no_metadata_field=False):
        if no_metadata_field:
            post_body = ""
        else:
            post_body = json.dumps({'metadata': meta})
        resp, body = self.put('servers/%s/metadata' % str(server_id),
                              post_body, self.headers)
        body = json.loads(body)
        return resp, body['metadata']

    def update_server_metadata(self, server_id, meta):
        post_body = json.dumps({'metadata': meta})
        resp, body = self.post('servers/%s/metadata' % str(server_id),
                               post_body, self.headers)
        body = json.loads(body)
        return resp, body['metadata']

    def get_server_metadata_item(self, server_id, key):
        resp, body = self.get("servers/%s/metadata/%s" % (str(server_id), key))
        body = json.loads(body)
        return resp, body['meta']

    def set_server_metadata_item(self, server_id, key, meta):
        post_body = json.dumps({'meta': meta})
        resp, body = self.put('servers/%s/metadata/%s' % (str(server_id), key),
                              post_body, self.headers)
        body = json.loads(body)
        return resp, body['meta']

    def delete_server_metadata_item(self, server_id, key):
        resp, body = self.delete("servers/%s/metadata/%s" %
                                 (str(server_id), key))
        return resp, body

    def stop(self, server_id, **kwargs):
        return self.action(server_id, 'os-stop', None, **kwargs)

    def start(self, server_id, **kwargs):
        return self.action(server_id, 'os-start', None, **kwargs)

    def attach_volume(self, server_id, volume_id, device='/dev/vdz'):
        """Attaches a volume to a server instance."""
        post_body = json.dumps({
            'volumeAttachment': {
                'volumeId': volume_id,
                'device': device,
            }
        })
        resp, body = self.post('servers/%s/os-volume_attachments' % server_id,
                               post_body, self.headers)
        return resp, body

    def detach_volume(self, server_id, volume_id):
        """Detaches a volume from a server instance."""
        resp, body = self.delete('servers/%s/os-volume_attachments/%s' %
                                 (server_id, volume_id))
        return resp, body

    def add_security_group(self, server_id, name):
        """Adds a security group to the server."""
        return self.action(server_id, 'addSecurityGroup', None, name=name)

    def remove_security_group(self, server_id, name):
        """Removes a security group from the server."""
        return self.action(server_id, 'removeSecurityGroup', None, name=name)

    def live_migrate_server(self, server_id, dest_host, use_block_migration):
        """This should be called with administrator privileges ."""

        migrate_params = {
            "disk_over_commit": False,
            "block_migration": use_block_migration,
            "host": dest_host
        }

        req_body = json.dumps({'os-migrateLive': migrate_params})

        resp, body = self.post("servers/%s/action" % str(server_id),
                               req_body, self.headers)
        return resp, body

    def migrate_server(self, server_id, **kwargs):
        """Migrates a server to a new host."""
        return self.action(server_id, 'migrate', None, **kwargs)

    def lock_server(self, server_id, **kwargs):
        """Locks the given server."""
        return self.action(server_id, 'lock', None, **kwargs)

    def unlock_server(self, server_id, **kwargs):
        """UNlocks the given server."""
        return self.action(server_id, 'unlock', None, **kwargs)

    def suspend_server(self, server_id, **kwargs):
        """Suspends the provded server."""
        return self.action(server_id, 'suspend', None, **kwargs)

    def resume_server(self, server_id, **kwargs):
        """Un-suspends the provded server."""
        return self.action(server_id, 'resume', None, **kwargs)

    def pause_server(self, server_id, **kwargs):
        """Pauses the provded server."""
        return self.action(server_id, 'pause', None, **kwargs)

    def unpause_server(self, server_id, **kwargs):
        """Un-pauses the provded server."""
        return self.action(server_id, 'unpause', None, **kwargs)

    def reset_state(self, server_id, state='error'):
        """Resets the state of a server to active/error."""
        return self.action(server_id, 'os-resetState', None, state=state)

    def get_console_output(self, server_id, length):
        return self.action(server_id, 'os-getConsoleOutput', 'output',
                           length=length)

    def list_virtual_interfaces(self, server_id):
        """
        List the virtual interfaces used in an instance.
        """
        resp, body = self.get('/'.join(['servers', server_id,
                              'os-virtual-interfaces']))
        return resp, json.loads(body)

    def rescue_server(self, server_id, adminPass=None):
        """Rescue the provided server."""
        return self.action(server_id, 'rescue', None, adminPass=adminPass)

    def unrescue_server(self, server_id):
        """Unrescue the provided server."""
        return self.action(server_id, 'unrescue', None)

    def list_instance_actions(self, server_id):
        """List the provided server action."""
        resp, body = self.get("servers/%s/os-instance-actions" %
                              str(server_id))
        body = json.loads(body)
        return resp, body['instanceActions']

    def get_instance_action(self, server_id, request_id):
        """Returns the action details of the provided server."""
        resp, body = self.get("servers/%s/os-instance-actions/%s" %
                              (str(server_id), str(request_id)))
        body = json.loads(body)
        return resp, body['instanceAction']
