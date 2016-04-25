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

import copy

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.api_schema.response.compute.v2_1 import servers as schema
from tempest.lib.api_schema.response.compute.v2_19 import servers as schemav219
from tempest.lib.api_schema.response.compute.v2_9 import servers as schemav29
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class ServersClient(base_compute_client.BaseComputeClient):
    schema_versions_info = [
        {'min': None, 'max': '2.8', 'schema': schema},
        {'min': '2.9', 'max': '2.18', 'schema': schemav29},
        {'min': '2.19', 'max': None, 'schema': schemav219}]

    def __init__(self, auth_provider, service, region,
                 enable_instance_password=True, **kwargs):
        super(ServersClient, self).__init__(
            auth_provider, service, region, **kwargs)
        self.enable_instance_password = enable_instance_password

    def create_server(self, **kwargs):
        """Create server.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#createServer

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

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#updateServer

        Most parameters except the following are passed to the API without
        any changes.
        :param disk_config: The name is changed to OS-DCF:diskConfig
        """
        if kwargs.get('disk_config'):
            kwargs['OS-DCF:diskConfig'] = kwargs.pop('disk_config')

        post_body = json.dumps({'server': kwargs})
        resp, body = self.put("servers/%s" % server_id, post_body)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.update_server, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_server(self, server_id):
        """Get server details."""
        resp, body = self.get("servers/%s" % server_id)
        body = json.loads(body)
        schema = self.get_schema(self.schema_versions_info)
        self.validate_response(schema.get_server, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_server(self, server_id):
        """Delete server."""
        resp, body = self.delete("servers/%s" % server_id)
        self.validate_response(schema.delete_server, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_servers(self, detail=False, **params):
        """List servers.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#listServers
                          and http://developer.openstack.org/
                              api-ref-compute-v2.1.html#listDetailServers
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
        """Lists all addresses for a server."""
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

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#createBackup
        """
        return self.action(server_id, "createBackup", **kwargs)

    def change_password(self, server_id, **kwargs):
        """Change the root password for the server.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#changePassword
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

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#reboot
        """
        return self.action(server_id, 'reboot', **kwargs)

    def rebuild_server(self, server_id, image_ref, **kwargs):
        """Rebuild a server with a new image.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#rebuild

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

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#resize

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

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#confirmResize
        """
        return self.action(server_id, 'confirmResize',
                           schema.server_actions_confirm_resize,
                           **kwargs)

    def revert_resize_server(self, server_id, **kwargs):
        """Revert a server back to its original flavor.

        Available params: see http://developer.openstack.org/
                              api-ref-compute-v2.1.html#revertResize
        """
        return self.action(server_id, 'revertResize', **kwargs)

    def list_server_metadata(self, server_id):
        resp, body = self.get("servers/%s/metadata" % server_id)
        body = json.loads(body)
        self.validate_response(schema.list_server_metadata, resp, body)
        return rest_client.ResponseBody(resp, body)

    def set_server_metadata(self, server_id, meta, no_metadata_field=False):
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
        post_body = json.dumps({'metadata': meta})
        resp, body = self.post('servers/%s/metadata' % server_id,
                               post_body)
        body = json.loads(body)
        self.validate_response(schema.update_server_metadata,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_server_metadata_item(self, server_id, key):
        resp, body = self.get("servers/%s/metadata/%s" % (server_id, key))
        body = json.loads(body)
        self.validate_response(schema.set_show_server_metadata_item,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def set_server_metadata_item(self, server_id, key, meta):
        post_body = json.dumps({'meta': meta})
        resp, body = self.put('servers/%s/metadata/%s' % (server_id, key),
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.set_show_server_metadata_item,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_server_metadata_item(self, server_id, key):
        resp, body = self.delete("servers/%s/metadata/%s" %
                                 (server_id, key))
        self.validate_response(schema.delete_server_metadata_item,
                               resp, body)
        return rest_client.ResponseBody(resp, body)

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
        """Detaches a volume from a server instance."""
        resp, body = self.delete('servers/%s/os-volume_attachments/%s' %
                                 (server_id, volume_id))
        self.validate_response(schema.detach_volume, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_volume_attachment(self, server_id, volume_id):
        """Return details about the given volume attachment."""
        resp, body = self.get('servers/%s/os-volume_attachments/%s' % (
            server_id, volume_id))
        body = json.loads(body)
        self.validate_response(schema.show_volume_attachment, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_volume_attachments(self, server_id):
        """Returns the list of volume attachments for a given instance."""
        resp, body = self.get('servers/%s/os-volume_attachments' % (
            server_id))
        body = json.loads(body)
        self.validate_response(schema.list_volume_attachments, resp, body)
        return rest_client.ResponseBody(resp, body)

    def add_security_group(self, server_id, **kwargs):
        """Add a security group to the server.

        Available params: TODO
        """
        # TODO(oomichi): The api-site doesn't contain this API description.
        # So the above should be changed to the api-site link after
        # adding the description on the api-site.
        # LP: https://bugs.launchpad.net/openstack-api-site/+bug/1524199
        return self.action(server_id, 'addSecurityGroup', **kwargs)

    def remove_security_group(self, server_id, **kwargs):
        """Remove a security group from the server.

        Available params: TODO
        """
        # TODO(oomichi): The api-site doesn't contain this API description.
        # So the above should be changed to the api-site link after
        # adding the description on the api-site.
        # LP: https://bugs.launchpad.net/openstack-api-site/+bug/1524199
        return self.action(server_id, 'removeSecurityGroup', **kwargs)

    def live_migrate_server(self, server_id, **kwargs):
        """This should be called with administrator privileges.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#migrateLive
        """
        return self.action(server_id, 'os-migrateLive', **kwargs)

    def migrate_server(self, server_id, **kwargs):
        """Migrate a server to a new host.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#migrate
        """
        return self.action(server_id, 'migrate', **kwargs)

    def lock_server(self, server_id, **kwargs):
        """Lock the given server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#lock
        """
        return self.action(server_id, 'lock', **kwargs)

    def unlock_server(self, server_id, **kwargs):
        """UNlock the given server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#unlock
        """
        return self.action(server_id, 'unlock', **kwargs)

    def suspend_server(self, server_id, **kwargs):
        """Suspend the provided server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#suspend
        """
        return self.action(server_id, 'suspend', **kwargs)

    def resume_server(self, server_id, **kwargs):
        """Un-suspend the provided server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#resume
        """
        return self.action(server_id, 'resume', **kwargs)

    def pause_server(self, server_id, **kwargs):
        """Pause the provided server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#pause
        """
        return self.action(server_id, 'pause', **kwargs)

    def unpause_server(self, server_id, **kwargs):
        """Un-pause the provided server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#unpause
        """
        return self.action(server_id, 'unpause', **kwargs)

    def reset_state(self, server_id, **kwargs):
        """Reset the state of a server to active/error.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#resetState
        """
        return self.action(server_id, 'os-resetState', **kwargs)

    def shelve_server(self, server_id, **kwargs):
        """Shelve the provided server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#shelve
        """
        return self.action(server_id, 'shelve', **kwargs)

    def unshelve_server(self, server_id, **kwargs):
        """Un-shelve the provided server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#unshelve
        """
        return self.action(server_id, 'unshelve', **kwargs)

    def shelve_offload_server(self, server_id, **kwargs):
        """Shelve-offload the provided server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#shelveOffload
        """
        return self.action(server_id, 'shelveOffload', **kwargs)

    def get_console_output(self, server_id, **kwargs):
        """Get console output.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#getConsoleOutput
        """
        return self.action(server_id, 'os-getConsoleOutput',
                           schema.get_console_output, **kwargs)

    def list_virtual_interfaces(self, server_id):
        """List the virtual interfaces used in an instance."""
        resp, body = self.get('/'.join(['servers', server_id,
                              'os-virtual-interfaces']))
        body = json.loads(body)
        self.validate_response(schema.list_virtual_interfaces, resp, body)
        return rest_client.ResponseBody(resp, body)

    def rescue_server(self, server_id, **kwargs):
        """Rescue the provided server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#rescue
        """
        return self.action(server_id, 'rescue', schema.rescue_server, **kwargs)

    def unrescue_server(self, server_id):
        """Unrescue the provided server."""
        return self.action(server_id, 'unrescue')

    def show_server_diagnostics(self, server_id):
        """Get the usage data for a server."""
        resp, body = self.get("servers/%s/diagnostics" % server_id)
        return rest_client.ResponseBody(resp, json.loads(body))

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

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#forceDelete
        """
        return self.action(server_id, 'forceDelete', **kwargs)

    def restore_soft_deleted_server(self, server_id, **kwargs):
        """Restore a soft-deleted server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#restore
        """
        return self.action(server_id, 'restore', **kwargs)

    def reset_network(self, server_id, **kwargs):
        """Reset the Network of a server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#resetNetwork
        """
        return self.action(server_id, 'resetNetwork', **kwargs)

    def inject_network_info(self, server_id, **kwargs):
        """Inject the Network Info into server.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#injectNetworkInfo
        """
        return self.action(server_id, 'injectNetworkInfo', **kwargs)

    def get_vnc_console(self, server_id, **kwargs):
        """Get URL of VNC console.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#getVNCConsole
        """
        return self.action(server_id, "os-getVNCConsole",
                           schema.get_vnc_console, **kwargs)

    def add_fixed_ip(self, server_id, **kwargs):
        """Add a fixed IP to server instance.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#addFixedIp
        """
        return self.action(server_id, 'addFixedIp', **kwargs)

    def remove_fixed_ip(self, server_id, **kwargs):
        """Remove input fixed IP from input server instance.

        Available params: http://developer.openstack.org/
                          api-ref-compute-v2.1.html#removeFixedIp
        """
        return self.action(server_id, 'removeFixedIp', **kwargs)
