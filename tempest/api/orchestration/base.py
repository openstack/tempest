# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.common import log as logging
import time

from tempest import clients
from tempest.common.utils.data_utils import rand_name
import tempest.test


LOG = logging.getLogger(__name__)


class BaseOrchestrationTest(tempest.test.BaseTestCase):
    """Base test case class for all Orchestration API tests."""

    @classmethod
    def setUpClass(cls):

        os = clients.OrchestrationManager()
        cls.orchestration_cfg = os.config.orchestration
        if not os.config.service_available.heat:
            raise cls.skipException("Heat support is required")
        cls.build_timeout = cls.orchestration_cfg.build_timeout
        cls.build_interval = cls.orchestration_cfg.build_interval

        cls.os = os
        cls.orchestration_client = os.orchestration_client
        cls.servers_client = os.servers_client
        cls.keypairs_client = os.keypairs_client
        cls.stacks = []
        cls.keypairs = []

    @classmethod
    def _get_identity_admin_client(cls):
        """
        Returns an instance of the Identity Admin API client
        """
        os = clients.AdminManager(interface=cls._interface)
        admin_client = os.identity_client
        return admin_client

    @classmethod
    def _get_client_args(cls):

        return (
            cls.config,
            cls.config.identity.admin_username,
            cls.config.identity.admin_password,
            cls.config.identity.uri
        )

    @classmethod
    def create_stack(cls, stack_name, template_data, parameters={}):
        resp, body = cls.client.create_stack(
            stack_name,
            template=template_data,
            parameters=parameters)
        stack_id = resp['location'].split('/')[-1]
        stack_identifier = '%s/%s' % (stack_name, stack_id)
        cls.stacks.append(stack_identifier)
        return stack_identifier

    @classmethod
    def clear_stacks(cls):
        for stack_identifier in cls.stacks:
            try:
                cls.orchestration_client.delete_stack(stack_identifier)
            except Exception:
                pass

        for stack_identifier in cls.stacks:
            try:
                cls.orchestration_client.wait_for_stack_status(
                    stack_identifier, 'DELETE_COMPLETE')
            except Exception:
                pass

    @classmethod
    def _create_keypair(cls, namestart='keypair-heat-'):
        kp_name = rand_name(namestart)
        resp, body = cls.keypairs_client.create_keypair(kp_name)
        cls.keypairs.append(kp_name)
        return body

    @classmethod
    def clear_keypairs(cls):
        for kp_name in cls.keypairs:
            try:
                cls.keypairs_client.delete_keypair(kp_name)
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        cls.clear_stacks()
        cls.clear_keypairs()

    def wait_for(self, condition):
        """Repeatedly calls condition() until a timeout."""
        start_time = int(time.time())
        while True:
            try:
                condition()
            except Exception:
                pass
            else:
                return
            if int(time.time()) - start_time >= self.build_timeout:
                condition()
                return
            time.sleep(self.build_interval)

    @staticmethod
    def stack_output(stack, output_key):
        """Return a stack output value for a give key."""
        return next((o['output_value'] for o in stack['outputs']
                    if o['output_key'] == output_key), None)
