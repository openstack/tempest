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
from oslo_log import log as logging

from tempest_lib.common.utils import misc as misc_utils

from tempest import config
from tempest import exceptions

CONF = config.CONF

LOG = logging.getLogger(__name__)


def get_network_from_name(name, compute_networks_client):
    """Get a full network dict from just a network name

    :param str name: the name of the network to use
    :param NetworksClientJSON compute_networks_client: The network client
        object to use for making the network lists api request
    :return: The full dictionary for the network in question
    :rtype: dict
    :raises InvalidConfiguration: If the name provided is invalid, the networks
        list returns a 404, there are no found networks, or the found network
        is invalid
    """
    caller = misc_utils.find_test_caller()

    if not name:
        raise exceptions.InvalidConfiguration()

    networks = compute_networks_client.list_networks()
    networks = [n for n in networks if n['label'] == name]

    # Check that a network exists, else raise an InvalidConfigurationException
    if len(networks) == 1:
        network = sorted(networks)[0]
    elif len(networks) > 1:
        msg = ("Network with name: %s had multiple matching networks in the "
               "list response: %s\n Unable to specify a single network" % (
                   name, networks))
        if caller:
            msg = '(%s) %s' % (caller, msg)
        LOG.warn(msg)
        raise exceptions.InvalidConfiguration()
    else:
        msg = "Network with name: %s not found" % name
        if caller:
            msg = '(%s) %s' % (caller, msg)
        LOG.warn(msg)
        raise exceptions.InvalidConfiguration()
    # To be consistent between neutron and nova network always use name even
    # if label is used in the api response. If neither is present than then
    # the returned network is invalid.
    name = network.get('name') or network.get('label')
    if not name:
        msg = "Network found from list doesn't contain a valid name or label"
        if caller:
            msg = '(%s) %s' % (caller, msg)
        LOG.warn(msg)
        raise exceptions.InvalidConfiguration()
    network['name'] = name
    return network


def get_tenant_network(creds_provider, compute_networks_client):
    """Get a network usable by the primary tenant

    :param creds_provider: instance of credential provider
    :param compute_networks_client: compute network client. We want to have the
           compute network client so we can have use a common approach for both
           neutron and nova-network cases. If this is not an admin network
           client, set_network_kwargs might fail in case fixed_network_name
           is the network to be used, and it's not visible to the tenant
    :return a dict with 'id' and 'name' of the network
    """
    caller = misc_utils.find_test_caller()
    fixed_network_name = CONF.compute.fixed_network_name
    net_creds = creds_provider.get_primary_creds()
    network = getattr(net_creds, 'network', None)
    if not network or not network.get('name'):
        if fixed_network_name:
            msg = ('No valid network provided or created, defaulting to '
                   'fixed_network_name')
            if caller:
                msg = '(%s) %s' % (caller, msg)
            LOG.debug(msg)
            try:
                network = get_network_from_name(fixed_network_name,
                                                compute_networks_client)
            except exceptions.InvalidConfiguration:
                network = {}
    msg = ('Found network %s available for tenant' % network)
    if caller:
        msg = '(%s) %s' % (caller, msg)
    LOG.info(msg)
    return network


def set_networks_kwarg(network, kwargs=None):
    """Set 'networks' kwargs for a server create if missing

    :param network: dict of network to be used with 'id' and 'name'
    :param kwargs: server create kwargs to be enhanced
    :return: new dict of kwargs updated to include networks
    """
    params = copy.copy(kwargs) or {}
    if kwargs and 'networks' in kwargs:
        return params

    if network:
        if 'id' in network.keys():
            params.update({"networks": [{'uuid': network['id']}]})
        else:
            LOG.warn('The provided network dict: %s was invalid and did not '
                     ' contain an id' % network)
    return params
