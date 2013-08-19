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

from tempest.common.utils.data_utils import rand_name
from tempest.openstack.common import log as logging
from tempest.scenario import manager

LOG = logging.getLogger(__name__)


class TestServerBasicOps(manager.OfficialClientTest):

    """
    This smoke test case follows this basic set of operations:

     * Create a keypair for use in launching an instance
     * Create a security group to control network access in instance
     * Add simple permissive rules to the security group
     * Launch an instance
     * Pause/unpause the instance
     * Suspend/resume the instance
     * Terminate the instance
    """

    def add_keypair(self):
        self.keypair = self.create_keypair()

    def create_security_group(self):
        sg_name = rand_name('secgroup-smoke')
        sg_desc = sg_name + " description"
        self.secgroup = self.compute_client.security_groups.create(sg_name,
                                                                   sg_desc)
        try:
            self.assertEqual(self.secgroup.name, sg_name)
            self.assertEqual(self.secgroup.description, sg_desc)
            self.set_resource('secgroup', self.secgroup)
        except AttributeError:
            self.fail("SecurityGroup object not successfully created.")

        # Add rules to the security group
        rulesets = [
            {
                'ip_protocol': 'tcp',
                'from_port': 1,
                'to_port': 65535,
                'cidr': '0.0.0.0/0',
                'group_id': self.secgroup.id
            },
            {
                'ip_protocol': 'icmp',
                'from_port': -1,
                'to_port': -1,
                'cidr': '0.0.0.0/0',
                'group_id': self.secgroup.id
            }
        ]
        for ruleset in rulesets:
            try:
                self.compute_client.security_group_rules.create(
                    self.secgroup.id, **ruleset)
            except Exception:
                self.fail("Failed to create rule in security group.")

    def boot_instance(self):
        create_kwargs = {
            'key_name': self.keypair.id
        }
        instance = self.create_server(self.compute_client,
                                      create_kwargs=create_kwargs)
        self.set_resource('instance', instance)

    def pause_server(self):
        instance = self.get_resource('instance')
        instance_id = instance.id
        LOG.debug("Pausing instance %s. Current status: %s",
                  instance_id, instance.status)
        instance.pause()
        self.status_timeout(
            self.compute_client.servers, instance_id, 'PAUSED')

    def unpause_server(self):
        instance = self.get_resource('instance')
        instance_id = instance.id
        LOG.debug("Unpausing instance %s. Current status: %s",
                  instance_id, instance.status)
        instance.unpause()
        self.status_timeout(
            self.compute_client.servers, instance_id, 'ACTIVE')

    def suspend_server(self):
        instance = self.get_resource('instance')
        instance_id = instance.id
        LOG.debug("Suspending instance %s. Current status: %s",
                  instance_id, instance.status)
        instance.suspend()
        self.status_timeout(self.compute_client.servers,
                            instance_id, 'SUSPENDED')

    def resume_server(self):
        instance = self.get_resource('instance')
        instance_id = instance.id
        LOG.debug("Resuming instance %s. Current status: %s",
                  instance_id, instance.status)
        instance.resume()
        self.status_timeout(
            self.compute_client.servers, instance_id, 'ACTIVE')

    def terminate_instance(self):
        instance = self.get_resource('instance')
        instance.delete()
        self.remove_resource('instance')

    def test_server_basicops(self):
        self.add_keypair()
        self.create_security_group()
        self.boot_instance()
        self.pause_server()
        self.unpause_server()
        self.suspend_server()
        self.resume_server()
        self.terminate_instance()
