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

from oslo_config import cfg
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
    compute_host_dict = CONF.ucsm.compute_host_dict
    controller_host_dict = CONF.ucsm.controller_host_dict
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
        cls.multi_ucsm_conf = parse_tempest_multi_ucsm_config(CONF.ucsm.ucsm_list)
        cls.ucsm_confs_with_vnic_templates = [ucsm for ucsm in cls.multi_ucsm_conf.values() if ucsm['vnic_template_dict']]
        cls.multi_ucsm_clients = {uc['ucsm_ip']: utils.UCSMClient(uc['ucsm_ip'], uc['ucsm_username'], uc['ucsm_password'])
                                  for uc in cls.multi_ucsm_conf.values()}

        cls.ucsm = utils.UCSMClient(cls.ucsm_ip, cls.ucsm_username,
                                    cls.ucsm_password)

    def ucsm_setup(self):
        self.ucsm.login()
        for c in self.multi_ucsm_clients.values():
            c.login()

    def ucsm_cleanup(self):
        self.ucsm.logout()
        for c in self.multi_ucsm_clients.values():
            c.logout()

    def _verify_connectivity_tests_enabled(self):
        if not CONF.ucsm.test_connectivity:
            raise self.skipException('Connectivity tests are not enabled. Update tempest.conf')

    def _verify_sriov_configured(self):
        if not CONF.ucsm.virtual_functions_amount:
            raise self.skipException('There are no SR-IOV ports. Update tempest.conf')

    def _verify_single_ucsm_configured(self):
        if not CONF.ucsm.compute_host_dict:
            raise self.skipException('There are no computes. Update tempest.conf')
        if not CONF.ucsm.controller_host_dict:
            raise self.skipException('There are no controllers. Update tempest.conf')
        if not CONF.ucsm.eth_names:
            raise self.skipException('There are no eth_names. Update tempest.conf')

    def _verify_multi_ucsm_configured(self, need_amount=None):
        if not CONF.ucsm.ucsm_list:
            raise self.skipException('CONF.ucsm.ucsm_list is empty. Please check Multi-UCSM parameters in tempest.conf')
        if need_amount and len(CONF.ucsm.ucsm_list) < need_amount:
            raise self.skipException('Not anough amount of UCSMs configured')

    def _verify_vnic_templates_configured(self, need_amount=None):
        self._verify_multi_ucsm_configured(need_amount=need_amount)
        if len(self.ucsm_confs_with_vnic_templates) == 0:
            raise self.skipException('vNIC templates are not configured. Update tempest.conf')
        if not CONF.ucsm.physnets:
            raise self.skipException('CONF.ucsm.physnets is empty. Update tempest.conf')
        if need_amount and len(self.ucsm_confs_with_vnic_templates) < need_amount:
            raise self.skipException('Not anough amount of UCSMs are using vNIC templates')

    def _verify_more_than_one_compute_host_exist(self):
        if not len(CONF.ucsm.compute_host_dict)>1:
            raise self.skipException('Only one compute host available. At least two required.')


def parse_tempest_multi_ucsm_config(ucsm_list):
    conf = cfg.ConfigOpts()

    config_groups = list()
    if ucsm_list:
        for ucsm in ucsm_list:
            group_name = 'ucsm:{0}'.format(ucsm)
            group_title = 'Options for UCSM {0}'.format(group_name)
            group = cfg.OptGroup(name=group_name, title=group_title)
            opts = [
                cfg.StrOpt('ucsm_ip', default=ucsm, help="UCSM username"),
                cfg.StrOpt('ucsm_username', help="UCSM username"),
                cfg.StrOpt('ucsm_password', help="UCSM password"),
                cfg.DictOpt('controller_host_dict', help="Dictionary <controller_hostname>:<service_profile>"),
                cfg.DictOpt('compute_host_dict', help="Dictionary <compute_hostname>:<service_profile>"),
                cfg.ListOpt('eth_names', default=['eth0', 'eth1'], help="eth names"),
                cfg.DictOpt('vnic_template_dict', help="vNIC templates"),
                cfg.IntOpt('virtual_functions_amount', help="Amount of virtual functions"),
            ]
            conf.register_opts(opts, group)
            config_groups.append(group)
    conf(args=[], project='ucsm_tests', default_config_files=CONF.default_config_files)
    return {conf[g.name]['ucsm_ip']: conf[g.name] for g in config_groups}
