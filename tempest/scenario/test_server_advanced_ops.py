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


from tempest.common.utils.data_utils import rand_name
from tempest.scenario import manager

LOG = logging.getLogger(__name__)


class TestServerAdvancedOps(manager.OfficialClientTest):

    """
    This test case stresses some advanced server instance operations:

     * Resizing an instance
    """

    @classmethod
    def setUpClass(cls):
        super(TestServerAdvancedOps, cls).setUpClass()

        if not cls.config.compute.resize_available:
            msg = "Skipping test - resize not available on this host"
            raise cls.skipException(msg)

        resize_flavor = cls.config.compute.flavor_ref_alt

        if resize_flavor == cls.config.compute.flavor_ref:
            msg = "Skipping test - flavor_ref and flavor_ref_alt are identical"
            raise cls.skipException(msg)

    @classmethod
    def tearDownClass(cls):
        for thing in cls.resources:
            thing.delete()

    def test_resize_server_confirm(self):
        # We create an instance for use in this test
        i_name = rand_name('instance')
        flavor_id = self.config.compute.flavor_ref
        base_image_id = self.config.compute.image_ref
        self.instance = self.compute_client.servers.create(
            i_name, base_image_id, flavor_id)
        try:
            self.assertEqual(self.instance.name, i_name)
            self.set_resource('instance', self.instance)
        except AttributeError:
            self.fail("Instance not successfully created.")

        self.assertEqual(self.instance.status, 'BUILD')
        instance_id = self.get_resource('instance').id
        self.status_timeout(
            self.compute_client.servers, instance_id, 'ACTIVE')
        instance = self.get_resource('instance')
        instance_id = instance.id
        resize_flavor = self.config.compute.flavor_ref_alt
        LOG.debug("Resizing instance %s from flavor %s to flavor %s",
                  instance.id, instance.flavor, resize_flavor)
        instance.resize(resize_flavor)
        self.status_timeout(self.compute_client.servers, instance_id,
                            'VERIFY_RESIZE')

        LOG.debug("Confirming resize of instance %s", instance_id)
        instance.confirm_resize()
        self.status_timeout(
            self.compute_client.servers, instance_id, 'ACTIVE')
