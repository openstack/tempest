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

import os.path

from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
import tempest.test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseOrchestrationTest(tempest.test.BaseTestCase):
    """Base test case class for all Orchestration API tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseOrchestrationTest, cls).setUpClass()
        cls.os = clients.Manager()
        if not CONF.service_available.heat:
            raise cls.skipException("Heat support is required")
        cls.build_timeout = CONF.orchestration.build_timeout
        cls.build_interval = CONF.orchestration.build_interval

        cls.orchestration_client = cls.os.orchestration_client
        cls.client = cls.orchestration_client
        cls.servers_client = cls.os.servers_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.network_client = cls.os.network_client
        cls.volumes_client = cls.os.volumes_client
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
        """Returns an instance of the Identity Admin API client."""
        manager = clients.AdminManager(interface=cls._interface)
        admin_client = manager.identity_client
        return admin_client

    @classmethod
    def create_stack(cls, stack_name, template_data, parameters={},
                     environment=None, files=None):
        resp, body = cls.client.create_stack(
            stack_name,
            template=template_data,
            parameters=parameters,
            environment=environment,
            files=files)
        stack_id = resp['location'].split('/')[-1]
        stack_identifier = '%s/%s' % (stack_name, stack_id)
        cls.stacks.append(stack_identifier)
        return stack_identifier

    @classmethod
    def _clear_stacks(cls):
        for stack_identifier in cls.stacks:
            try:
                cls.client.delete_stack(stack_identifier)
            except exceptions.NotFound:
                pass

        for stack_identifier in cls.stacks:
            try:
                cls.client.wait_for_stack_status(
                    stack_identifier, 'DELETE_COMPLETE')
            except exceptions.NotFound:
                pass

    @classmethod
    def _create_keypair(cls, name_start='keypair-heat-'):
        kp_name = data_utils.rand_name(name_start)
        resp, body = cls.keypairs_client.create_keypair(kp_name)
        cls.keypairs.append(kp_name)
        return body

    @classmethod
    def _clear_keypairs(cls):
        for kp_name in cls.keypairs:
            try:
                cls.keypairs_client.delete_keypair(kp_name)
            except Exception:
                pass

    @classmethod
    def load_template(cls, name, ext='yaml'):
        loc = ["stacks", "templates", "%s.%s" % (name, ext)]
        fullpath = os.path.join(os.path.dirname(__file__), *loc)

        with open(fullpath, "r") as f:
            content = f.read()
            return content

    @classmethod
    def tearDownClass(cls):
        cls._clear_stacks()
        cls._clear_keypairs()
        super(BaseOrchestrationTest, cls).tearDownClass()

    @staticmethod
    def stack_output(stack, output_key):
        """Return a stack output value for a given key."""
        return next((o['output_value'] for o in stack['outputs']
                    if o['output_key'] == output_key), None)

    def assert_fields_in_dict(self, obj, *fields):
        for field in fields:
            self.assertIn(field, obj)

    def list_resources(self, stack_identifier):
        """Get a dict mapping of resource names to types."""
        resp, resources = self.client.list_resources(stack_identifier)
        self.assertEqual('200', resp['status'])
        self.assertIsInstance(resources, list)
        for res in resources:
            self.assert_fields_in_dict(res, 'logical_resource_id',
                                       'resource_type', 'resource_status',
                                       'updated_time')

        return dict((r['resource_name'], r['resource_type'])
                    for r in resources)

    def get_stack_output(self, stack_identifier, output_key):
        resp, body = self.client.get_stack(stack_identifier)
        self.assertEqual('200', resp['status'])
        return self.stack_output(body, output_key)
