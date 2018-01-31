# Copyright 2012 OpenStack Foundation
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2017 AT&T Corp.
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

import copy

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.api_schema.response.compute.v2_1 import \
    security_groups as security_groups_schema
from tempest.lib.api_schema.response.compute.v2_1 import servers as schema
from tempest.lib.api_schema.response.compute.v2_16 import servers as schemav216
from tempest.lib.api_schema.response.compute.v2_19 import servers as schemav219
from tempest.lib.api_schema.response.compute.v2_26 import servers as schemav226
from tempest.lib.api_schema.response.compute.v2_3 import servers as schemav23
from tempest.lib.api_schema.response.compute.v2_47 import servers as schemav247
from tempest.lib.api_schema.response.compute.v2_48 import servers as schemav248
from tempest.lib.api_schema.response.compute.v2_6 import servers as schemav26
from tempest.lib.api_schema.response.compute.v2_9 import servers as schemav29
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class ServersClient(base_compute_client.BaseComputeClient):
    """Service client for the resource /servers"""

    schema_versions_info = [
        {'min': None, 'max': '2.2', 'schema': schema},
        {'min': '2.3', 'max': '2.5', 'schema': schemav23},
        {'min': '2.6', 'max': '2.8', 'schema': schemav26},
        {'min': '2.9', 'max': '2.15', 'schema': schemav29},
        {'min': '2.16', 'max': '2.18', 'schema': schemav216},
        {'min': '2.19', 'max': '2.25', 'schema': schemav219},
        {'min': '2.26', 'max': '2.46', 'schema': schemav226},
        {'min': '2.47', 'max': '2.47', 'schema': schemav247},
        {'min': '2.48', 'max': None, 'schema': schemav248}]

    def __init__(self, auth_provider, service, region,
                 enable_instance_password=True, **kwargs):
        super(ServersClient, self).__init__(
            auth_provider, service, region, **kwargs)
        self.enable_instance_password = enable_instance_password

    def create_server(self, **kwargs):
        """Create server.

        For a full list of available parameters, please refer to the official
        API reference:
        http://developer.openstack.org/api-ref/compute/#create-server

        :param name: Server name
        :param imageRef: Image reference (UUID)
        :param flavorRef: Flavor reference (UUID or full URL)

        Most parameters except the following are passed to the API without
        any changes.
        :param disk_config: The name is changed to OS-DCF:diskConfig
        :param scheduler_hints: The name is changed to os:scheduler_hints and
        the parameter is set in the same level as the parameter 'server'.
        """
        body = copy.deepcopy(kwargs)
        if body.get('disk_config'):
            body['OS-DCF:diskConfig'] = body.pop('disk_config')

        hints = None
        if body.get('scheduler_hints'):
            hints = {'os:scheduler_hints': body.pop('scheduler_hints')}

        post_body = {'server': body}

        if hints:
            post_body.update(hints)

        post_body = json.dumps(post_body)
        resp, body = self.post('servers', post_body)

        body = json.loads(body)
        # NOTE(maurosr): this deals with the case of multiple server create
        # with return reservation id set True
        if 'reservation_id' in body:
            return rest_client.ResponseBody(resp, body)
        if self.enable_instance_password:
            create_schema = schema.create_server_with_admin_pass
        else:
            create_schema = schema.create_server
        self.validate_response(create_schema, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_server(self, server_id, **kwargs):
        """Update server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#update-server

        Most parameters except the following are passed to the API without
        any changes.
        :param disk_config: The name is changed to OS-DCF:diskConfig
        """
        if 'disk_config' in kwargs:
            kwargs['OS-DCF:diskConfig'] = kwargs.pop('disk_config')

        post_body = json.dumps({'server': kwargs})
        resp, body = self.put("servers/%s" % server_id, post_body)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.update_server, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_server(self, server_id):
        """Get server details.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#show-server-details
        """
        resp, body = self.get("servers/%s" % server_id)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.get_server, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_server(self, server_id):
        """Delete server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#delete-server
        """
        resp, body = self.delete("servers/%s" % server_id)
        self.validate_response(schema.delete_server, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_servers(self, detail=False, **params):
        """List servers.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#list-servers
        https://developer.openstack.org/api-ref/compute/#list-servers-detailed
        """

        url = 'servers'
        schema = self.get_schema(self.schema_versions_info)
        _schema = schema.list_servers

        if detail:
            url += '/detail'
            _schema = schema.list_servers_detail
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(_schema, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_addresses(self, server_id):
        """Lists all addresses for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#list-ips
        """
        resp, body = self.get("servers/%s/ips" % server_id)
        body = json.loads(body)
        self.validate_response(schema.list_addresses, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_addresses_by_network(self, server_id, network_id):
        """Lists all addresses of a specific network type for a server."""
        resp, body = self.get("servers/%s/ips/%s" %
                              (server_id, network_id))
        body = json.loads(body)
        self.validate_response(schema.list_addresses_by_network, resp, body)
        return rest_client.ResponseBody(resp, body)

    def action(self, server_id, action_name,
               schema=schema.server_actions_common_schema,
               **kwargs):
        post_body = json.dumps({action_name: kwargs})
        resp, body = self.post('servers/%s/action' % server_id,
                               post_body)
        if body:
            body = json.loads(body)
        self.validate_response(schema, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_backup(self, server_id, **kwargs):
        """Backup a server instance.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#create-server-back-up-createbackup-action
        """
        return self.action(server_id, "createBackup", **kwargs)

    def change_password(self, server_id, **kwargs):
        """Change the root password for the server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#change-administrative-password-changepassword-action
        """
        return self.action(server_id, 'changePassword', **kwargs)

    def show_password(self, server_id):
        resp, body = self.get("servers/%s/os-server-password" %
                              server_id)
        body = json.loads(body)
        self.validate_response(schema.show_password, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_password(self, server_id):
        """Removes the encrypted server password from the metadata server

        Note that this does not actually change the instance server
        password.
        """
        resp, body = self.delete("servers/%s/os-server-password" %
                                 server_id)
        self.validate_response(schema.server_actions_delete_password,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def reboot_server(self, server_id, **kwargs):
        """Reboot a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#reboot-server-reboot-action
        """
        return self.action(server_id, 'reboot', **kwargs)

    def rebuild_server(self, server_id, image_ref, **kwargs):
        """Rebuild a server with a new image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#rebuild-server-rebuild-action

        Most parameters except the following are passed to the API without
        any changes.
        :param disk_config: The name is changed to OS-DCF:diskConfig
        """
        kwargs['imageRef'] = image_ref
        if 'disk_config' in kwargs:
            kwargs['OS-DCF:diskConfig'] = kwargs.pop('disk_config')
        schema = self.get_schema(self.schema_versions_info)
        if self.enable_instance_password:
            rebuild_schema = schema.rebuild_server_with_admin_pass
        else:
            rebuild_schema = schema.rebuild_server
        return self.action(server_id, 'rebuild',
                           rebuild_schema, **kwargs)

    def resize_server(self, server_id, flavor_ref, **kwargs):
        """Change the flavor of a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#resize-server-resize-action

        Most parameters except the following are passed to the API without
        any changes.
        :param disk_config: The name is changed to OS-DCF:diskConfig
        """
        kwargs['flavorRef'] = flavor_ref
        if 'disk_config' in kwargs:
            kwargs['OS-DCF:diskConfig'] = kwargs.pop('disk_config')
        return self.action(server_id, 'resize', **kwargs)

    def confirm_resize_server(self, server_id, **kwargs):
        """Confirm the flavor change for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#confirm-resized-server-confirmresize-action
        """
        return self.action(server_id, 'confirmResize',
                           schema.server_actions_confirm_resize,
                           **kwargs)

    def revert_resize_server(self, server_id, **kwargs):
        """Revert a server back to its original flavor.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#revert-resized-server-revertresize-action
        """
        return self.action(server_id, 'revertResize', **kwargs)

    def list_server_metadata(self, server_id):
        """Lists all metadata for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#list-all-metadata
        """
        resp, body = self.get("servers/%s/metadata" % server_id)
        body = json.loads(body)
        self.validate_response(schema.list_server_metadata, resp, body)
        return rest_client.ResponseBody(resp, body)

    def set_server_metadata(self, server_id, meta, no_metadata_field=False):
        """Sets one or more metadata items for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#replace-metadata-items
        """
        if no_metadata_field:
            post_body = ""
        else:
            post_body = json.dumps({'metadata': meta})
        resp, body = self.put('servers/%s/metadata' % server_id,
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.set_server_metadata, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_server_metadata(self, server_id, meta):
        """Updates one or more metadata items for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#create-or-update-metadata-items
        """
        post_body = json.dumps({'metadata': meta})
        resp, body = self.post('servers/%s/metadata' % server_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.update_server_metadata,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_server_metadata_item(self, server_id, key):
        """Shows details for a metadata item, by key, for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#show-metadata-item-details
        """
        resp, body = self.get("servers/%s/metadata/%s" % (server_id, key))
        body = json.loads(body)
        self.validate_response(schema.set_show_server_metadata_item,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def set_server_metadata_item(self, server_id, key, meta):
        """Sets a metadata item, by key, for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#create-or-update-metadata-item
        """
        post_body = json.dumps({'meta': meta})
        resp, body = self.put('servers/%s/metadata/%s' % (server_id, key),
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.set_show_server_metadata_item,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_server_metadata_item(self, server_id, key):
        """Deletes a metadata item, by key, from a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#delete-metadata-item
        """
        resp, body = self.delete("servers/%s/metadata/%s" %
                                 (server_id, key))
        self.validate_response(schema.delete_server_metadata_item,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def stop_server(self, server_id, **kwargs):
        """Stops a running server and changes its status to SHUTOFF.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#stop-server-os-stop-action
        """
        return self.action(server_id, 'os-stop', **kwargs)

    def start_server(self, server_id, **kwargs):
        """Starts a stopped server and changes its status to ACTIVE.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#start-server-os-start-action
        """
        return self.action(server_id, 'os-start', **kwargs)

    def attach_volume(self, server_id, **kwargs):
        """Attaches a volume to a server instance.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#attach-a-volume-to-an-instance
        """
        post_body = json.dumps({'volumeAttachment': kwargs})
        resp, body = self.post('servers/%s/os-volume_attachments' % server_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.attach_volume, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_attached_volume(self, server_id, attachment_id, **kwargs):
        """Swaps a volume attached to an instance for another volume"""
        post_body = json.dumps({'volumeAttachment': kwargs})
        resp, body = self.put('servers/%s/os-volume_attachments/%s' %
                              (server_id, attachment_id),
                              post_body)
        self.validate_response(schema.update_attached_volume, resp, body)
        return rest_client.ResponseBody(resp, body)

    def detach_volume(self, server_id, volume_id):  # noqa
        """Detaches a volume from a server instance.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#detach-a-volume-from-an-instance
        """
        resp, body = self.delete('servers/%s/os-volume_attachments/%s' %
                                 (server_id, volume_id))
        self.validate_response(schema.detach_volume, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_volume_attachment(self, server_id, volume_id):
        """Return details about the given volume attachment.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#show-a-detail-of-a-volume-attachment
        """
        resp, body = self.get('servers/%s/os-volume_attachments/%s' % (
            server_id, volume_id))
        body = json.loads(body)
        self.validate_response(schema.show_volume_attachment, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_volume_attachments(self, server_id):
        """Returns the list of volume attachments for a given instance.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#list-volume-attachments-for-an-instance
        """
        resp, body = self.get('servers/%s/os-volume_attachments' % (
            server_id))
        body = json.loads(body)
        self.validate_response(schema.list_volume_attachments, resp, body)
        return rest_client.ResponseBody(resp, body)

    def add_security_group(self, server_id, **kwargs):
        """Add a security group to the server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#add-security-group-to-a-server-addsecuritygroup-action
        """
        return self.action(server_id, 'addSecurityGroup', **kwargs)

    def remove_security_group(self, server_id, **kwargs):
        """Remove a security group from the server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#remove-security-group-from-a-server-removesecuritygroup-action
        """
        return self.action(server_id, 'removeSecurityGroup', **kwargs)

    def live_migrate_server(self, server_id, **kwargs):
        """This should be called with administrator privileges.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#live-migrate-server-os-migratelive-action
        """
        return self.action(server_id, 'os-migrateLive', **kwargs)

    def migrate_server(self, server_id, **kwargs):
        """Migrate a server to a new host.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#migrate-server-migrate-action
        """
        return self.action(server_id, 'migrate', **kwargs)

    def lock_server(self, server_id, **kwargs):
        """Lock the given server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#lock-server-lock-action
        """
        return self.action(server_id, 'lock', **kwargs)

    def unlock_server(self, server_id, **kwargs):
        """UNlock the given server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#unlock-server-unlock-action
        """
        return self.action(server_id, 'unlock', **kwargs)

    def suspend_server(self, server_id, **kwargs):
        """Suspend the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#suspend-server-suspend-action
        """
        return self.action(server_id, 'suspend', **kwargs)

    def resume_server(self, server_id, **kwargs):
        """Un-suspend the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#resume-suspended-server-resume-action
        """
        return self.action(server_id, 'resume', **kwargs)

    def pause_server(self, server_id, **kwargs):
        """Pause the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#pause-server-pause-action
        """
        return self.action(server_id, 'pause', **kwargs)

    def unpause_server(self, server_id, **kwargs):
        """Un-pause the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#unpause-server-unpause-action
        """
        return self.action(server_id, 'unpause', **kwargs)

    def reset_state(self, server_id, **kwargs):
        """Reset the state of a server to active/error.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#reset-server-state-os-resetstate-action
        """
        return self.action(server_id, 'os-resetState', **kwargs)

    def shelve_server(self, server_id, **kwargs):
        """Shelve the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#shelve-server-shelve-action
        """
        return self.action(server_id, 'shelve', **kwargs)

    def unshelve_server(self, server_id, **kwargs):
        """Un-shelve the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#unshelve-restore-shelved-server-unshelve-action
        """
        return self.action(server_id, 'unshelve', **kwargs)

    def shelve_offload_server(self, server_id, **kwargs):
        """Shelve-offload the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#shelf-offload-remove-server-shelveoffload-action
        """
        return self.action(server_id, 'shelveOffload', **kwargs)

    def get_console_output(self, server_id, **kwargs):
        """Get console output.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#show-console-output-os-getconsoleoutput-action
        """
        return self.action(server_id, 'os-getConsoleOutput',
                           schema.get_console_output, **kwargs)

    def get_remote_console(self, server_id, console_type, protocol, **kwargs):
        """Get a remote console.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#create-remote-console
        """
        param = {
            'remote_console': {
                'type': console_type,
                'protocol': protocol,
            }
        }
        post_body = json.dumps(param)
        resp, body = self.post("servers/%s/remote-consoles" % server_id,
                               post_body)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.get_remote_consoles, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_virtual_interfaces(self, server_id):
        """List the virtual interfaces used in an instance."""
        resp, body = self.get('/'.join(['servers', server_id,
                              'os-virtual-interfaces']))
        body = json.loads(body)
        self.validate_response(schema.list_virtual_interfaces, resp, body)
        return rest_client.ResponseBody(resp, body)

    def rescue_server(self, server_id, **kwargs):
        """Rescue the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#rescue-server-rescue-action
        """
        if self.enable_instance_password:
            rescue_schema = schema.rescue_server_with_admin_pass
        else:
            rescue_schema = schema.rescue_server
        return self.action(server_id, 'rescue', rescue_schema, **kwargs)

    def unrescue_server(self, server_id):
        """Unrescue the provided server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#unrescue-server-unrescue-action
        """
        return self.action(server_id, 'unrescue')

    def show_server_diagnostics(self, server_id):
        """Get the usage data for a server."""
        resp, body = self.get("servers/%s/diagnostics" % server_id)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.show_server_diagnostics, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_instance_actions(self, server_id):
        """List the provided server action."""
        resp, body = self.get("servers/%s/os-instance-actions" %
                              server_id)
        body = json.loads(body)
        self.validate_response(schema.list_instance_actions, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_instance_action(self, server_id, request_id):
        """Returns the action details of the provided server."""
        resp, body = self.get("servers/%s/os-instance-actions/%s" %
                              (server_id, request_id))
        body = json.loads(body)
        self.validate_response(schema.show_instance_action, resp, body)
        return rest_client.ResponseBody(resp, body)

    def force_delete_server(self, server_id, **kwargs):
        """Force delete a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#force-delete-server-forcedelete-action
        """
        return self.action(server_id, 'forceDelete', **kwargs)

    def restore_soft_deleted_server(self, server_id, **kwargs):
        """Restore a soft-deleted server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#restore-soft-deleted-instance-restore-action
        """
        return self.action(server_id, 'restore', **kwargs)

    def reset_network(self, server_id, **kwargs):
        """Reset the Network of a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#reset-networking-on-a-server-resetnetwork-action
        """
        return self.action(server_id, 'resetNetwork', **kwargs)

    def inject_network_info(self, server_id, **kwargs):
        """Inject the Network Info into server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#inject-network-information-injectnetworkinfo-action
        """
        return self.action(server_id, 'injectNetworkInfo', **kwargs)

    def get_vnc_console(self, server_id, **kwargs):
        """Get URL of VNC console.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#get-vnc-console-os-getvncconsole-action-deprecated
        """
        return self.action(server_id, "os-getVNCConsole",
                           schema.get_vnc_console, **kwargs)

    def add_fixed_ip(self, server_id, **kwargs):
        """Add a fixed IP to server instance.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#add-associate-fixed-ip-addfixedip-action-deprecated
        """
        return self.action(server_id, 'addFixedIp', **kwargs)

    def remove_fixed_ip(self, server_id, **kwargs):
        """Remove input fixed IP from input server instance.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#remove-disassociate-fixed-ip-removefixedip-action-deprecated
        """
        return self.action(server_id, 'removeFixedIp', **kwargs)

    def list_security_groups_by_server(self, server_id):
        """Lists security groups for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#list-security-groups-by-server
        """
        resp, body = self.get("servers/%s/os-security-groups" % server_id)
        body = json.loads(body)
        self.validate_response(security_groups_schema.list_security_groups,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_tags(self, server_id):
        """Lists all tags for a server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#list-tags
        """
        url = 'servers/%s/tags' % server_id
        resp, body = self.get(url)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.list_tags, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_all_tags(self, server_id, tags):
        """Replaces all tags on specified server with the new set of tags.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#replace-tags

        :param tags: List of tags to replace current server tags with.
        """
        url = 'servers/%s/tags' % server_id
        put_body = {'tags': tags}
        resp, body = self.put(url, json.dumps(put_body))
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.update_all_tags, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_all_tags(self, server_id):
        """Deletes all tags from the specified server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#delete-all-tags
        """
        url = 'servers/%s/tags' % server_id
        resp, body = self.delete(url)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.delete_all_tags, resp, body)
        return rest_client.ResponseBody(resp, body)

    def check_tag_existence(self, server_id, tag):
        """Checks tag existence on the server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#check-tag-existence

        :param tag: Check for existence of tag on specified server.
        """
        url = 'servers/%s/tags/%s' % (server_id, tag)
        resp, body = self.get(url)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.check_tag_existence, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_tag(self, server_id, tag):
        """Adds a single tag to the server if server has no specified tag.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#add-a-single-tag

        :param tag: Tag to be added to the specified server.
        """
        url = 'servers/%s/tags/%s' % (server_id, tag)
        resp, body = self.put(url, None)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.update_tag, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_tag(self, server_id, tag):
        """Deletes a single tag from the specified server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#delete-a-single-tag

        :param tag: Tag to be removed from the specified server.
        """
        url = 'servers/%s/tags/%s' % (server_id, tag)
        resp, body = self.delete(url)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.delete_tag, resp, body)
        return rest_client.ResponseBody(resp, body)

    def evacuate_server(self, server_id, **kwargs):
        """Evacuate the given server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#evacuate-server-evacuate-action
        """
        if self.enable_instance_password:
            evacuate_schema = schema.evacuate_server_with_admin_pass
        else:
            evacuate_schema = schema.evacuate_server

        return self.action(server_id, 'evacuate',
                           evacuate_schema,
                           **kwargs)
