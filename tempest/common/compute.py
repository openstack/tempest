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
from tempest_lib.common.utils import data_utils

from tempest.common import fixed_network
from tempest.common import service_client
from tempest.common import waiters
from tempest import config

CONF = config.CONF

LOG = logging.getLogger(__name__)


def create_test_server(clients, validatable=False, validation_resources=None,
                       tenant_network=None, wait_until=None, **kwargs):
    """Common wrapper utility returning a test server.

    This method is a common wrapper returning a test server that can be
    pingable or sshable.

    :param clients: Client manager which provides Openstack Tempest clients.
    :param validatable: Whether the server will be pingable or sshable.
    :param validation_resources: Resources created for the connection to the
    server. Include a keypair, a security group and an IP.
    :param tenant_network: Tenant network to be used for creating a server.
    :param wait_until: Server status to wait for the server to reach after
    its creation.
    :returns a tuple
    """

    # TODO(jlanoux) add support of wait_until PINGABLE/SSHABLE

    if 'name' in kwargs:
        name = kwargs.pop('name')
    else:
        name = data_utils.rand_name(__name__ + "-instance")

    flavor = kwargs.get('flavor', CONF.compute.flavor_ref)
    image_id = kwargs.get('image_id', CONF.compute.image_ref)

    kwargs = fixed_network.set_networks_kwarg(
        tenant_network, kwargs) or {}

    if CONF.validation.run_validation and validatable:
        # As a first implementation, multiple pingable or sshable servers will
        # not be supported
        if 'min_count' in kwargs or 'max_count' in kwargs:
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

    body = clients.servers_client.create_server(name, image_id, flavor,
                                                **kwargs)

    # handle the case of multiple servers
    servers = []
    if 'min_count' in kwargs or 'max_count' in kwargs:
        # Get servers created which name match with name param.
        body_servers = clients.servers_client.list_servers()
        servers = \
            [s for s in body_servers['servers'] if s['name'].startswith(name)]
    else:
        body = service_client.ResponseBody(body.response, body['server'])
        servers = [body]

    # The name of the method to associate a floating IP to as server is too
    # long for PEP8 compliance so:
    assoc = clients.floating_ips_client.associate_floating_ip_to_server

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
                    if ('preserve_server_on_error' not in kwargs
                        or kwargs['preserve_server_on_error'] is False):
                        for server in servers:
                            try:
                                clients.servers_client.delete_server(
                                    server['id'])
                            except Exception:
                                LOG.exception('Deleting server %s failed'
                                              % server['id'])

    return body, servers
