# Copyright (c) 2014 Deutsche Telekom AG
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

import abc

import six

from tempest import config
from tempest.openstack.common import log as logging

CONF = config.CONF
LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class CredentialProvider(object):
    def __init__(self, name, interface='json', password='pass',
                 network_resources=None):
        self.name = name

    @abc.abstractmethod
    def get_primary_creds(self):
        return

    @abc.abstractmethod
    def get_admin_creds(self):
        return

    @abc.abstractmethod
    def get_alt_creds(self):
        return

    @abc.abstractmethod
    def clear_isolated_creds(self):
        return

    @abc.abstractmethod
    def is_multi_user(self):
        return

    @abc.abstractmethod
    def is_multi_tenant(self):
        return
