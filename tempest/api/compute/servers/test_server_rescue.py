# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import testtools

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ServerRescueTestBase(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(ServerRescueTestBase, cls).skip_checks()
        if not CONF.compute_feature_enabled.rescue:
            msg = "Server rescue not available."
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources(network=True, subnet=True, router=True)
        super(ServerRescueTestBase, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(ServerRescueTestBase, cls).resource_setup()

        password = data_utils.rand_password()
        server = cls.create_test_server(adminPass=password,
                                        wait_until='ACTIVE')
        cls.servers_client.rescue_server(server['id'], adminPass=password)
        waiters.wait_for_server_status(cls.servers_client, server['id'],
                                       'RESCUE')
        cls.rescued_server_id = server['id']


class ServerRescueTestJSON(ServerRescueTestBase):

    @decorators.idempotent_id('fd032140-714c-42e4-a8fd-adcd8df06be6')
    def test_rescue_unrescue_instance(self):
        password = data_utils.rand_password()
        server = self.create_test_server(adminPass=password,
                                         wait_until='ACTIVE')
        self.servers_client.rescue_server(server['id'], adminPass=password)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'RESCUE')
        self.servers_client.unrescue_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')


class ServerRescueTestJSONUnderV235(ServerRescueTestBase):

    max_microversion = '2.35'

    # TODO(zhufl): After 2.35 we should switch to neutron client to create
    # floating ip, but that will need admin credential, so the testcases will
    # have to be added in somewhere in admin directory.

    @decorators.idempotent_id('4842e0cf-e87d-4d9d-b61f-f4791da3cacc')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    @testtools.skipUnless(CONF.network_feature_enabled.floating_ips,
                          "Floating ips are not available")
    def test_rescued_vm_associate_dissociate_floating_ip(self):
        # Association of floating IP to a rescued vm
        floating_ip_body = self.floating_ips_client.create_floating_ip(
            pool=CONF.network.floating_network_name)['floating_ip']
        self.addCleanup(self.floating_ips_client.delete_floating_ip,
                        floating_ip_body['id'])

        self.floating_ips_client.associate_floating_ip_to_server(
            str(floating_ip_body['ip']).strip(), self.rescued_server_id)

        # Disassociation of floating IP that was associated in this method
        self.floating_ips_client.disassociate_floating_ip_from_server(
            str(floating_ip_body['ip']).strip(), self.rescued_server_id)

    @decorators.idempotent_id('affca41f-7195-492d-8065-e09eee245404')
    def test_rescued_vm_add_remove_security_group(self):
        # Add Security group
        sg = self.create_security_group()
        self.servers_client.add_security_group(self.rescued_server_id,
                                               name=sg['name'])

        # Delete Security group
        self.servers_client.remove_security_group(self.rescued_server_id,
                                                  name=sg['name'])
