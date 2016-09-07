# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

from functools import partial

from tempest import config
from tempest.lib.common.utils import data_utils as lib_data_utils

CONF = config.CONF

PING_IPV4_COMMAND = 'ping -c 3 '
PING_IPV6_COMMAND = 'ping6 -c 3 '
PING_PACKET_LOSS_REGEX = '(\d{1,3})\.?\d*\% packet loss'


class DataUtils(object):
    def __getattr__(self, attr):

        if attr == 'rand_name':
            # NOTE(flwang): This is a proxy to generate a random name that
            # includes a random number and a prefix if one is configured in
            # CONF.resources_prefix
            attr_obj = partial(lib_data_utils.rand_name,
                               prefix=CONF.resources_prefix)
        else:
            attr_obj = getattr(lib_data_utils, attr)

        self.__dict__[attr] = attr_obj
        return attr_obj

data_utils = DataUtils()
