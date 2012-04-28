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

import logging

from tempest import test

LOG = logging.getLogger(__name__)


class SmokeTest(object):

    """
    Base test case class mixin for "smoke tests"

    Smoke tests are tests that have the following characteristics:

     * Test basic operations of an API, typically in an order that
       a regular user would perform those operations
     * Test only the correct inputs and action paths -- no fuzz or
       random input data is sent, only valid inputs.
     * Use only the default client tool for calling an API
    """
    pass


class ComputeSmokeTest(test.ComputeDefaultClientTest, SmokeTest):

    """
    Base smoke test case class for OpenStack Compute API (Nova)
    """

    @classmethod
    def tearDownClass(cls):
        # NOTE(jaypipes): Because smoke tests are typically run in a specific
        # order, and because test methods in smoke tests generally create
        # resources in a particular order, we destroy resources in the reverse
        # order in which resources are added to the smoke test class object
        if not cls.resources:
            return
        thing = cls.resources.pop()
        while True:
            LOG.debug("Deleting %r from shared resources of %s" %
                      (thing, cls.__name__))
            # Resources in novaclient all have a delete() method
            # which destroys the resource...
            thing.delete()
            if not cls.resources:
                return
            thing = cls.resources.pop()
