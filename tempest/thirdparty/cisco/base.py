# Copyright 2015 OpenStack Foundation
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

import random
import time
import types

from tempest import config
from tempest.thirdparty.cisco import utils

CONF = config.CONF


class UCSMTestMixin(object):
    """
    The mixing contains UCSM specific attributes and methods.

    Note: The tempest.conf should contain parameters:
    [ucsm]
    ucsm_ip={ucsm_ip}
    ucsm_username={ucsm_username}
    ucsm_password={ucsm_password}
    ucsm_host_dict={ucsm_host_list hostname:service-profile,...}
    network_node_host={hostname of a network_node}
    eth_names=eth0,eth1
    virtual_functions_amount=4
    """

    ucsm_ip = CONF.ucsm.ucsm_ip
    ucsm_username = CONF.ucsm.ucsm_username
    ucsm_password = CONF.ucsm.ucsm_password
    ucsm_host_dict = None
    network_node_list = CONF.ucsm.network_node_list
    network_node_host = CONF.ucsm.network_node_list[0]
    eth_names = CONF.ucsm.eth_names
    virtual_functions = CONF.ucsm.virtual_functions_amount

    def timed_assert(self, assert_func, *args):
        new_args = list()
        start_time = time.time()
        while time.time() - start_time < CONF.network.build_timeout:
            try:
                new_args = list()
                for arg in args:
                    new_args.append(
                        arg() if isinstance(arg, types.FunctionType) else arg)
                return assert_func(*new_args)
            except AssertionError:
                time.sleep(CONF.network.build_interval)
        return assert_func(*new_args)

    @classmethod
    def ucsm_resource_setup(cls):
        cls.ucsm = utils.UCSMClient(cls.ucsm_ip, cls.ucsm_username,
                                    cls.ucsm_password)
        cls.ucsm_host_dict = \
            {k: 'org-root/ls-' + v
             for k, v in CONF.ucsm.ucsm_host_dict.iteritems()}
        cls.network_node_profile = cls.ucsm_host_dict[cls.network_node_host]

        compute_hosts = set(cls.ucsm_host_dict.keys()) - set(cls.network_node_list)
        if len(compute_hosts) > 1:
            smpl = random.sample(compute_hosts, 2)
            cls.master_host = smpl[0]
            cls.slave_host = smpl[1]
        else:
            cls.master_host = compute_hosts[0]
            cls.slave_host = None

    def ucsm_setup(self):
        self.ucsm.login()

    def ucsm_cleanup(self):
        self.ucsm.logout()
