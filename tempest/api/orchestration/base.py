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

from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
import tempest.test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseOrchestrationTest(tempest.test.BaseTestCase):
    """Base test case class for all Orchestration API tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseOrchestrationTest, cls).setUpClass()
        os = clients.OrchestrationManager()
        if not CONF.service_available.heat:
            raise cls.skipException("Heat support is required")
        cls.build_timeout = CONF.orchestration.build_timeout
        cls.build_interval = CONF.orchestration.build_interval

        cls.os = os
        cls.orchestration_client = os.orchestration_client
        cls.servers_client = os.servers_client
        cls.keypairs_client = os.keypairs_client
        cls.network_client = os.network_client
        cls.stacks = []
        cls.keypairs = []

    @classmethod
    def _get_default_network(cls):
        resp, networks = cls.network_client.list_networks()
        for net in networks['networks']:
            if net['name'] == CONF.compute.fixed_network_name:
                return net

    @classmethod
    def _get_identity_admin_client(cls):
        """
        Returns an instance of the Identity Admin API client
        """
        os = clients.AdminManager(interface=cls._interface)
        admin_client = os.identity_client
        return admin_client

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
    def _create_keypair(cls, name_start='keypair-heat-'):
        kp_name = data_utils.rand_name(name_start)
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
        super(BaseOrchestrationTest, cls).tearDownClass()

    @staticmethod
    def stack_output(stack, output_key):
        """Return a stack output value for a give key."""
        return next((o['output_value'] for o in stack['outputs']
                    if o['output_key'] == output_key), None)
