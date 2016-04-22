# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from oslo_log import log as logging
from oslo_utils import excutils

from tempest.common import fixed_network
from tempest.common import waiters
from tempest import config
from tempest.lib.common import rest_client
from tempest.lib.common.utils import data_utils

CONF = config.CONF

LOG = logging.getLogger(__name__)


def create_test_server(clients, validatable=False, validation_resources=None,
                       tenant_network=None, wait_until=None,
                       volume_backed=False, name=None, flavor=None,
                       image_id=None, **kwargs):
    """Common wrapper utility returning a test server.

    This method is a common wrapper returning a test server that can be
    pingable or sshable.

    :param clients: Client manager which provides OpenStack Tempest clients.
    :param validatable: Whether the server will be pingable or sshable.
    :param validation_resources: Resources created for the connection to the
    server. Include a keypair, a security group and an IP.
    :param tenant_network: Tenant network to be used for creating a server.
    :param wait_until: Server status to wait for the server to reach after
    its creation.
    :param volume_backed: Whether the instance is volume backed or not.
    :returns: a tuple
    """

    # TODO(jlanoux) add support of wait_until PINGABLE/SSHABLE

    if name is None:
        name = data_utils.rand_name(__name__ + "-instance")
    if flavor is None:
        flavor = CONF.compute.flavor_ref
    if image_id is None:
        image_id = CONF.compute.image_ref

    kwargs = fixed_network.set_networks_kwarg(
        tenant_network, kwargs) or {}

    multiple_create_request = (max(kwargs.get('min_count', 0),
                                   kwargs.get('max_count', 0)) > 1)

    if CONF.validation.run_validation and validatable:
        # As a first implementation, multiple pingable or sshable servers will
        # not be supported
        if multiple_create_request:
            msg = ("Multiple pingable or sshable servers not supported at "
                   "this stage.")
            raise ValueError(msg)

        if 'security_groups' in kwargs:
            kwargs['security_groups'].append(
                {'name': validation_resources['security_group']['name']})
        else:
            try:
                kwargs['security_groups'] = [
                    {'name': validation_resources['security_group']['name']}]
            except KeyError:
                LOG.debug("No security group provided.")

        if 'key_name' not in kwargs:
            try:
                kwargs['key_name'] = validation_resources['keypair']['name']
            except KeyError:
                LOG.debug("No key provided.")

        if CONF.validation.connect_method == 'floating':
            if wait_until is None:
                wait_until = 'ACTIVE'

    if volume_backed:
        volume_name = data_utils.rand_name('volume')
        volumes_client = clients.volumes_v2_client
        if CONF.volume_feature_enabled.api_v1:
            volumes_client = clients.volumes_client
        volume = volumes_client.create_volume(
            display_name=volume_name,
            imageRef=image_id)
        waiters.wait_for_volume_status(volumes_client,
                                       volume['volume']['id'], 'available')

        bd_map_v2 = [{
            'uuid': volume['volume']['id'],
            'source_type': 'volume',
            'destination_type': 'volume',
            'boot_index': 0,
            'delete_on_termination': True}]
        kwargs['block_device_mapping_v2'] = bd_map_v2

        # Since this is boot from volume an image does not need
        # to be specified.
        image_id = ''

    body = clients.servers_client.create_server(name=name, imageRef=image_id,
                                                flavorRef=flavor,
                                                **kwargs)

    # handle the case of multiple servers
    servers = []
    if multiple_create_request:
        # Get servers created which name match with name param.
        body_servers = clients.servers_client.list_servers()
        servers = \
            [s for s in body_servers['servers'] if s['name'].startswith(name)]
    else:
        body = rest_client.ResponseBody(body.response, body['server'])
        servers = [body]

    # The name of the method to associate a floating IP to as server is too
    # long for PEP8 compliance so:
    assoc = clients.compute_floating_ips_client.associate_floating_ip_to_server

    if wait_until:
        for server in servers:
            try:
                waiters.wait_for_server_status(
                    clients.servers_client, server['id'], wait_until)

                # Multiple validatable servers are not supported for now. Their
                # creation will fail with the condition above (l.58).
                if CONF.validation.run_validation and validatable:
                    if CONF.validation.connect_method == 'floating':
                        assoc(floating_ip=validation_resources[
                              'floating_ip']['ip'],
                              server_id=servers[0]['id'])

            except Exception:
                with excutils.save_and_reraise_exception():
                    for server in servers:
                        try:
                            clients.servers_client.delete_server(
                                server['id'])
                        except Exception:
                            LOG.exception('Deleting server %s failed'
                                          % server['id'])

    return body, servers


def shelve_server(client, server_id, force_shelve_offload=False):
    """Common wrapper utility to shelve server.

    This method is a common wrapper to make server in 'SHELVED'
    or 'SHELVED_OFFLOADED' state.

    :param server_id: Server to make in shelve state
    :param force_shelve_offload: Forcefully offload shelve server if it
                                 is configured not to offload server
                                 automatically after offload time.
    """
    client.shelve_server(server_id)

    offload_time = CONF.compute.shelved_offload_time
    if offload_time >= 0:
        waiters.wait_for_server_status(client, server_id,
                                       'SHELVED_OFFLOADED',
                                       extra_timeout=offload_time)
    else:
        waiters.wait_for_server_status(client, server_id, 'SHELVED')
        if force_shelve_offload:
            client.shelve_offload_server(server_id)
            waiters.wait_for_server_status(client, server_id,
                                           'SHELVED_OFFLOADED')
