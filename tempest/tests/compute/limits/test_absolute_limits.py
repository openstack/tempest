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

import unittest2 as unittest

from tempest.tests.compute import base


class AbsoluteLimitsTest(object):

    @staticmethod
    def setUpClass(cls):
        cls.client = cls.limits_client

    @unittest.skip("Skipped until the Bug #1025294 is resolved")
    def test_absLimits_get(self):
        """
        To check if all limits are present in the response
        """
        resp, absolute_limits = self.client.get_absolute_limits()
        expected_elements = ['maxImageMeta', 'maxPersonality',
                             'maxPersonalitySize',
                             'maxPersonalityFilePathSize',
                             'maxServerMeta', 'maxTotalCores',
                             'maxTotalFloatingIps', 'maxSecurityGroups',
                             'maxSecurityGroupRules', 'maxTotalInstances',
                             'maxTotalKeypairs', 'maxTotalRAMSize',
                             'maxTotalVolumeGigabytes', 'maxTotalVolumes',
                             'totalCoresUsed', 'totalFloatingIpsUsed',
                             'totalSecurityGroupsUsed', 'totalInstancesUsed',
                             'totalKeyPairsUsed', 'totalRAMUsed',
                             'totalVolumeGigabytesUsed', 'totalVolumesUsed']
        # check whether all expected elements exist
        missing_elements =\
            [ele for ele in expected_elements if ele not in absolute_limits]
        self.assertEqual(0, len(missing_elements),
                         "Failed to find element %s in absolute limits list"
                         % ', '.join(ele for ele in missing_elements))


class AbsoluteLimitsTestJSON(base.BaseComputeTestJSON,
                             AbsoluteLimitsTest):
    @classmethod
    def setUpClass(cls):
        super(AbsoluteLimitsTestJSON, cls).setUpClass()
        AbsoluteLimitsTest.setUpClass(cls)


class AbsoluteLimitsTestXML(base.BaseComputeTestXML,
                            AbsoluteLimitsTest):
    @classmethod
    def setUpClass(cls):
        super(AbsoluteLimitsTestXML, cls).setUpClass()
        AbsoluteLimitsTest.setUpClass(cls)
