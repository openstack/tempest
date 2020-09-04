# Copyright 2012 OpenStack Foundation
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

from oslo_log import log as logging

from tempest import clients as tempest_clients
from tempest import config
from tempest.lib.services import clients

CONF = config.CONF
LOG = logging.getLogger(__name__)


class Manager(clients.ServiceClients):
    """Service client manager class for backward compatibility

    The former manager.Manager is not a stable interface in Tempest,
    nonetheless it is consumed by a number of plugins already. This class
    exists to provide some grace time for the move to tempest.lib.
    """

    def __init__(self, credentials, scope='project'):
        msg = ("tempest.manager.Manager is not a stable interface and as such "
               "it should not be imported directly. It will be removed as "
               "soon as the client manager becomes available in tempest.lib.")
        LOG.warning(msg)
        dscv = CONF.identity.disable_ssl_certificate_validation
        _, uri = tempest_clients.get_auth_provider_class(credentials)
        super(Manager, self).__init__(
            credentials=credentials, scope=scope,
            identity_uri=uri,
            disable_ssl_certificate_validation=dscv,
            ca_certs=CONF.identity.ca_certificates_file,
            trace_requests=CONF.debug.trace_requests)


def get_auth_provider(credentials, pre_auth=False, scope='project'):
    """Shim to get_auth_provider in clients.py

    get_auth_provider used to be hosted in this module, but it has been
    moved to clients.py now as a more permanent location.
    This module will be removed eventually, and this shim is only
    maintained for the benefit of plugins already consuming this interface.
    """
    msg = ("tempest.manager.get_auth_provider is not a stable interface and "
           "as such it should not imported directly. It will be removed as "
           "the client manager becomes available in tempest.lib.")
    LOG.warning(msg)
    return tempest_clients.get_auth_provider(credentials=credentials,
                                             pre_auth=pre_auth, scope=scope)
