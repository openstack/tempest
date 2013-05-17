# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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
from tempest import exceptions
from tempest.test import attr


class AbsoluteLimitsTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(AbsoluteLimitsTestJSON, cls).setUpClass()
        cls.client = cls.limits_client
        cls.server_client = cls.servers_client

    def test_absLimits_get(self):
        # To check if all limits are present in the response
        resp, absolute_limits = self.client.get_absolute_limits()
        expected_elements = ['maxImageMeta', 'maxPersonality',
                             'maxPersonalitySize',
                             'maxServerMeta', 'maxTotalCores',
                             'maxTotalFloatingIps', 'maxSecurityGroups',
                             'maxSecurityGroupRules', 'maxTotalInstances',
                             'maxTotalKeypairs', 'maxTotalRAMSize',
                             'totalCoresUsed', 'totalFloatingIpsUsed',
                             'totalSecurityGroupsUsed', 'totalInstancesUsed',
                             'totalRAMUsed']
        # check whether all expected elements exist
        missing_elements =\
            [ele for ele in expected_elements if ele not in absolute_limits]
        self.assertEqual(0, len(missing_elements),
                         "Failed to find element %s in absolute limits list"
                         % ', '.join(ele for ele in missing_elements))

    @attr(type='negative')
    def test_max_image_meta_exceed_limit(self):
        #We should not create vm with image meta over maxImageMeta limit
        # Get max limit value
        max_meta = self.client.get_specific_absolute_limit('maxImageMeta')

        #Create server should fail, since we are passing > metadata Limit!
        max_meta_data = int(max_meta) + 1

        meta_data = {}
        for xx in range(max_meta_data):
            meta_data[str(xx)] = str(xx)

        self.assertRaises(exceptions.OverLimit,
                          self.server_client.create_server,
                          name='test', meta=meta_data, flavor_ref='84',
                          image_ref='9e6a2e3b-1601-42a5-985f-c3a2f93a5ec3')


class AbsoluteLimitsTestXML(AbsoluteLimitsTestJSON):
    _interface = 'xml'
