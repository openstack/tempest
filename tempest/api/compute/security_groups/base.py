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

from tempest.api.compute import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils

CONF = config.CONF


class BaseSecurityGroupsTest(base.BaseV2ComputeTest):
    max_microversion = '2.35'

    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(BaseSecurityGroupsTest, cls).skip_checks()
        if not utils.get_service_list()['network']:
            raise cls.skipException("network service not enabled.")

    @staticmethod
    def generate_random_security_group_id():
        if (CONF.service_available.neutron and
            utils.is_extension_enabled('security-group', 'network')):
            return data_utils.rand_uuid()
        else:
            return data_utils.rand_int_id(start=999)
