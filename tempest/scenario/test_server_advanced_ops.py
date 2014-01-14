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

from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest.test import services

LOG = logging.getLogger(__name__)


class TestServerAdvancedOps(manager.OfficialClientTest):

    """
    This test case stresses some advanced server instance operations:

     * Resizing an instance
     * Sequence suspend resume
    """

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(TestServerAdvancedOps, cls).setUpClass()

        if not cls.config.compute_feature_enabled.resize:
            msg = "Skipping test - resize not available on this host"
            raise cls.skipException(msg)

        resize_flavor = cls.config.compute.flavor_ref_alt

        if resize_flavor == cls.config.compute.flavor_ref:
            msg = "Skipping test - flavor_ref and flavor_ref_alt are identical"
            raise cls.skipException(msg)

    @services('compute')
    def test_resize_server_confirm(self):
        # We create an instance for use in this test
        instance = self.create_server()
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

    @services('compute')
    def test_server_sequence_suspend_resume(self):
        # We create an instance for use in this test
        instance = self.create_server()
        instance_id = instance.id
        LOG.debug("Suspending instance %s. Current status: %s",
                  instance_id, instance.status)
        instance.suspend()
        self.status_timeout(self.compute_client.servers, instance_id,
                            'SUSPENDED')
        LOG.debug("Resuming instance %s. Current status: %s",
                  instance_id, instance.status)
        instance.resume()
        self.status_timeout(self.compute_client.servers, instance_id,
                            'ACTIVE')
        LOG.debug("Suspending instance %s. Current status: %s",
                  instance_id, instance.status)
        instance.suspend()
        self.status_timeout(self.compute_client.servers, instance_id,
                            'SUSPENDED')
        LOG.debug("Resuming instance %s. Current status: %s",
                  instance_id, instance.status)
        instance.resume()
        self.status_timeout(self.compute_client.servers, instance_id,
                            'ACTIVE')
