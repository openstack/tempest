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

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.api_schema.response.compute.v2_1 import servers as schema
from tempest.common import service_client


class ServersClient(service_client.ServiceClient):

    def __init__(self, auth_provider, service, region,
                 enable_instance_password=True, **kwargs):
        super(ServersClient, self).__init__(
            auth_provider, service, region, **kwargs)
        self.enable_instance_password = enable_instance_password

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
        block_device_mapping: Block device mapping for the server.
        block_device_mapping_v2: Block device mapping V2 for the server.
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
                       'return_reservation_id', 'block_device_mapping',
                       'block_device_mapping_v2']:
            if isinstance(option, tuple):
                post_param = option[0]
                key = option[1]
            else:
                post_param = option
                key = option
            value = kwargs.get(key)
            if value is not None:
                post_body[post_param] = value

        post_body = {'server': post_body}

        if 'sched_hints' in kwargs:
            hints = {'os:scheduler_hints': kwargs.get('sched_hints')}
            post_body = dict(post_body.items() + hints.items())
        post_body = json.dumps(post_body)
        resp, body = self.post('servers', post_body)

        body = json.loads(body)
        # NOTE(maurosr): this deals with the case of multiple server create
        # with return reservation id set True
        if 'reservation_id' in body:
            return service_client.ResponseBody(resp, body)
        if self.enable_instance_password:
            create_schema = schema.create_server_with_admin_pass
        else:
            create_schema = schema.create_server
        self.validate_response(create_schema, resp, body)
        return service_client.ResponseBody(resp, body)

    def update_server(self, server_id, **kwargs):
        """Updates the properties of an existing server.
        Most parameters except the following are passed to the API without
        any changes.
        :param disk_config: The name is changed to OS-DCF:diskConfig
        """
        if kwargs.get('disk_config'):
            kwargs['OS-DCF:diskConfig'] = kwargs.pop('disk_config')

        post_body = json.dumps({'server': kwargs})
        resp, body = self.put("servers/%s" % server_id, post_body)
        body = json.loads(body)
        self.validate_response(schema.update_server, resp, body)
        return service_client.ResponseBody(resp, body)

    def show_server(self, server_id):
        """Returns the details of an existing server."""
        resp, body = self.get("servers/%s" % server_id)
        body = json.loads(body)
        self.validate_response(schema.get_server, resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_server(self, server_id):
        """Deletes the given server."""
        resp, body = self.delete("servers/%s" % server_id)
        self.validate_response(schema.delete_server, resp, body)
        return service_client.ResponseBody(resp, body)

    def list_servers(self, detail=False, **params):
        """Lists all servers for a user."""

        url = 'servers'
        _schema = schema.list_servers

        if detail:
            url += '/detail'
            _schema = schema.list_servers_detail
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(_schema, resp, body)
        return service_client.ResponseBody(resp, body)

    def list_addresses(self, server_id):
        """Lists all addresses for a server."""
        resp, body = self.get("servers/%s/ips" % server_id)
        body = json.loads(body)
        self.validate_response(schema.list_addresses, resp, body)
        return service_client.ResponseBody(resp, body)

    def list_addresses_by_network(self, server_id, network_id):
        """Lists all addresses of a specific network type for a server."""
        resp, body = self.get("servers/%s/ips/%s" %
                              (server_id, network_id))
        body = json.loads(body)
        self.validate_response(schema.list_addresses_by_network, resp, body)
        return service_client.ResponseBody(resp, body)

    def action(self, server_id, action_name,
               schema=schema.server_actions_common_schema,
               **kwargs):
        post_body = json.dumps({action_name: kwargs})
        resp, body = self.post('servers/%s/action' % server_id,
                               post_body)
        if body:
            body = json.loads(body)
        self.validate_response(schema, resp, body)
        return service_client.ResponseBody(resp, body)

    def create_backup(self, server_id, backup_type, rotation, name):
        """Backup a server instance."""
        return self.action(server_id, "createBackup",
                           backup_type=backup_type,
                           rotation=rotation,
                           name=name)

    def change_password(self, server_id, adminPass):
        """Changes the root password for the server."""
        return self.action(server_id, 'changePassword',
                           adminPass=adminPass)

    def get_password(self, server_id):
        resp, body = self.get("servers/%s/os-server-password" %
                              server_id)
        body = json.loads(body)
        self.validate_response(schema.get_password, resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_password(self, server_id):
        """
        Removes the encrypted server password from the metadata server
        Note that this does not actually change the instance server
        password.
        """
        resp, body = self.delete("servers/%s/os-server-password" %
                                 server_id)
        self.validate_response(schema.server_actions_delete_password,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def reboot_server(self, server_id, reboot_type):
        """Reboots a server."""
        return self.action(server_id, 'reboot', type=reboot_type)

    def rebuild_server(self, server_id, image_ref, **kwargs):
        """Rebuilds a server with a new image.
        Most parameters except the following are passed to the API without
        any changes.
        :param disk_config: The name is changed to OS-DCF:diskConfig
        """
        kwargs['imageRef'] = image_ref
        if 'disk_config' in kwargs:
            kwargs['OS-DCF:diskConfig'] = kwargs.pop('disk_config')
        if self.enable_instance_password:
            rebuild_schema = schema.rebuild_server_with_admin_pass
        else:
            rebuild_schema = schema.rebuild_server
        return self.action(server_id, 'rebuild',
                           rebuild_schema, **kwargs)

    def resize_server(self, server_id, flavor_ref, **kwargs):
        """Changes the flavor of a server.
        Most parameters except the following are passed to the API without
        any changes.
        :param disk_config: The name is changed to OS-DCF:diskConfig
        """
        kwargs['flavorRef'] = flavor_ref
        if 'disk_config' in kwargs:
            kwargs['OS-DCF:diskConfig'] = kwargs.pop('disk_config')
        return self.action(server_id, 'resize', **kwargs)

    def confirm_resize_server(self, server_id, **kwargs):
        """Confirms the flavor change for a server."""
        return self.action(server_id, 'confirmResize',
                           schema.server_actions_confirm_resize,
                           **kwargs)

    def revert_resize_server(self, server_id, **kwargs):
        """Reverts a server back to its original flavor."""
        return self.action(server_id, 'revertResize', **kwargs)

    def list_server_metadata(self, server_id):
        resp, body = self.get("servers/%s/metadata" % server_id)
        body = json.loads(body)
        self.validate_response(schema.list_server_metadata, resp, body)
        return service_client.ResponseBody(resp, body)

    def set_server_metadata(self, server_id, meta, no_metadata_field=False):
        if no_metadata_field:
            post_body = ""
        else:
            post_body = json.dumps({'metadata': meta})
        resp, body = self.put('servers/%s/metadata' % server_id,
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.set_server_metadata, resp, body)
        return service_client.ResponseBody(resp, body)

    def update_server_metadata(self, server_id, meta):
        post_body = json.dumps({'metadata': meta})
        resp, body = self.post('servers/%s/metadata' % server_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.update_server_metadata,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def get_server_metadata_item(self, server_id, key):
        resp, body = self.get("servers/%s/metadata/%s" % (server_id, key))
        body = json.loads(body)
        self.validate_response(schema.set_get_server_metadata_item,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def set_server_metadata_item(self, server_id, key, meta):
        post_body = json.dumps({'meta': meta})
        resp, body = self.put('servers/%s/metadata/%s' % (server_id, key),
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.set_get_server_metadata_item,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_server_metadata_item(self, server_id, key):
        resp, body = self.delete("servers/%s/metadata/%s" %
                                 (server_id, key))
        self.validate_response(schema.delete_server_metadata_item,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def stop_server(self, server_id, **kwargs):
        return self.action(server_id, 'os-stop', **kwargs)

    def start_server(self, server_id, **kwargs):
        return self.action(server_id, 'os-start', **kwargs)

    def attach_volume(self, server_id, **kwargs):
        """Attaches a volume to a server instance."""
        post_body = json.dumps({'volumeAttachment': kwargs})
        resp, body = self.post('servers/%s/os-volume_attachments' % server_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.attach_volume, resp, body)
        return service_client.ResponseBody(resp, body)

    def detach_volume(self, server_id, volume_id):
        """Detaches a volume from a server instance."""
        resp, body = self.delete('servers/%s/os-volume_attachments/%s' %
                                 (server_id, volume_id))
        self.validate_response(schema.detach_volume, resp, body)
        return service_client.ResponseBody(resp, body)

    def get_volume_attachment(self, server_id, attach_id):
        """Return details about the given volume attachment."""
        resp, body = self.get('servers/%s/os-volume_attachments/%s' % (
            server_id, attach_id))
        body = json.loads(body)
        self.validate_response(schema.get_volume_attachment, resp, body)
        return service_client.ResponseBody(resp, body)

    def list_volume_attachments(self, server_id):
        """Returns the list of volume attachments for a given instance."""
        resp, body = self.get('servers/%s/os-volume_attachments' % (
            server_id))
        body = json.loads(body)
        self.validate_response(schema.list_volume_attachments, resp, body)
        return service_client.ResponseBody(resp, body)

    def add_security_group(self, server_id, name):
        """Adds a security group to the server."""
        return self.action(server_id, 'addSecurityGroup', name=name)

    def remove_security_group(self, server_id, name):
        """Removes a security group from the server."""
        return self.action(server_id, 'removeSecurityGroup', name=name)

    def live_migrate_server(self, server_id, **kwargs):
        """This should be called with administrator privileges ."""

        req_body = json.dumps({'os-migrateLive': kwargs})

        resp, body = self.post("servers/%s/action" % server_id, req_body)
        self.validate_response(schema.server_actions_common_schema,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def migrate_server(self, server_id, **kwargs):
        """Migrates a server to a new host."""
        return self.action(server_id, 'migrate', **kwargs)

    def lock_server(self, server_id, **kwargs):
        """Locks the given server."""
        return self.action(server_id, 'lock', **kwargs)

    def unlock_server(self, server_id, **kwargs):
        """UNlocks the given server."""
        return self.action(server_id, 'unlock', **kwargs)

    def suspend_server(self, server_id, **kwargs):
        """Suspends the provided server."""
        return self.action(server_id, 'suspend', **kwargs)

    def resume_server(self, server_id, **kwargs):
        """Un-suspends the provided server."""
        return self.action(server_id, 'resume', **kwargs)

    def pause_server(self, server_id, **kwargs):
        """Pauses the provided server."""
        return self.action(server_id, 'pause', **kwargs)

    def unpause_server(self, server_id, **kwargs):
        """Un-pauses the provided server."""
        return self.action(server_id, 'unpause', **kwargs)

    def reset_state(self, server_id, state='error'):
        """Resets the state of a server to active/error."""
        return self.action(server_id, 'os-resetState', state=state)

    def shelve_server(self, server_id, **kwargs):
        """Shelves the provided server."""
        return self.action(server_id, 'shelve', **kwargs)

    def unshelve_server(self, server_id, **kwargs):
        """Un-shelves the provided server."""
        return self.action(server_id, 'unshelve', **kwargs)

    def shelve_offload_server(self, server_id, **kwargs):
        """Shelve-offload the provided server."""
        return self.action(server_id, 'shelveOffload', **kwargs)

    def get_console_output(self, server_id, length):
        kwargs = {'length': length} if length else {}
        return self.action(server_id, 'os-getConsoleOutput',
                           schema.get_console_output,
                           **kwargs)

    def list_virtual_interfaces(self, server_id):
        """
        List the virtual interfaces used in an instance.
        """
        resp, body = self.get('/'.join(['servers', server_id,
                              'os-virtual-interfaces']))
        body = json.loads(body)
        self.validate_response(schema.list_virtual_interfaces, resp, body)
        return service_client.ResponseBody(resp, body)

    def rescue_server(self, server_id, **kwargs):
        """Rescue the provided server."""
        return self.action(server_id, 'rescue',
                           schema.rescue_server,
                           **kwargs)

    def unrescue_server(self, server_id):
        """Unrescue the provided server."""
        return self.action(server_id, 'unrescue')

    def get_server_diagnostics(self, server_id):
        """Get the usage data for a server."""
        resp, body = self.get("servers/%s/diagnostics" % server_id)
        return service_client.ResponseBody(resp, json.loads(body))

    def list_instance_actions(self, server_id):
        """List the provided server action."""
        resp, body = self.get("servers/%s/os-instance-actions" %
                              server_id)
        body = json.loads(body)
        self.validate_response(schema.list_instance_actions, resp, body)
        return service_client.ResponseBody(resp, body)

    def get_instance_action(self, server_id, request_id):
        """Returns the action details of the provided server."""
        resp, body = self.get("servers/%s/os-instance-actions/%s" %
                              (server_id, request_id))
        body = json.loads(body)
        self.validate_response(schema.get_instance_action, resp, body)
        return service_client.ResponseBody(resp, body)

    def force_delete_server(self, server_id, **kwargs):
        """Force delete a server."""
        return self.action(server_id, 'forceDelete', **kwargs)

    def restore_soft_deleted_server(self, server_id, **kwargs):
        """Restore a soft-deleted server."""
        return self.action(server_id, 'restore', **kwargs)

    def reset_network(self, server_id, **kwargs):
        """Resets the Network of a server"""
        return self.action(server_id, 'resetNetwork', **kwargs)

    def inject_network_info(self, server_id, **kwargs):
        """Inject the Network Info into server"""
        return self.action(server_id, 'injectNetworkInfo', **kwargs)

    def get_vnc_console(self, server_id, console_type):
        """Get URL of VNC console."""
        return self.action(server_id, "os-getVNCConsole",
                           schema.get_vnc_console,
                           type=console_type)

    def add_fixed_ip(self, server_id, **kwargs):
        """Add a fixed IP to input server instance."""
        return self.action(server_id, 'addFixedIp', **kwargs)

    def remove_fixed_ip(self, server_id, **kwargs):
        """Remove input fixed IP from input server instance."""
        return self.action(server_id, 'removeFixedIp', **kwargs)
