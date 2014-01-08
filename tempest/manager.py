# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest import config
from tempest import exceptions


class Manager(object):

    """
    Base manager class

    Manager objects are responsible for providing a configuration object
    and a client object for a test case to use in performing actions.
    """

    def __init__(self):
        self.config = config.CONF
        self.client_attr_names = []

    # we do this everywhere, have it be part of the super class
    def _validate_credentials(self, username, password, tenant_name):
        if None in (username, password, tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(u)s, password: %(p)s, "
                   "tenant_name: %(t)s" %
                   {'u': username, 'p': password, 't': tenant_name})
            raise exceptions.InvalidConfiguration(msg)
