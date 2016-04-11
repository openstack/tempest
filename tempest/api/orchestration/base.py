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

import yaml

from tempest.common.utils import data_utils
from tempest import config
from tempest.lib import exceptions as lib_exc
import tempest.test

CONF = config.CONF


class BaseOrchestrationTest(tempest.test.BaseTestCase):
    """Base test case class for all Orchestration API tests."""

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseOrchestrationTest, cls).skip_checks()
        if not CONF.service_available.heat:
            raise cls.skipException("Heat support is required")

    @classmethod
    def setup_credentials(cls):
        super(BaseOrchestrationTest, cls).setup_credentials()
        stack_owner_role = CONF.orchestration.stack_owner_role
        cls.os = cls.get_client_manager(roles=[stack_owner_role])

    @classmethod
    def setup_clients(cls):
        super(BaseOrchestrationTest, cls).setup_clients()
        cls.orchestration_client = cls.os.orchestration_client
        cls.client = cls.orchestration_client
        cls.servers_client = cls.os.servers_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.networks_client = cls.os.networks_client
        cls.volumes_client = cls.os.volumes_client
        cls.images_v2_client = cls.os.image_client_v2

        if CONF.volume_feature_enabled.api_v2:
            cls.volumes_client = cls.os.volumes_v2_client
        else:
            cls.volumes_client = cls.os.volumes_client

    @classmethod
    def resource_setup(cls):
        super(BaseOrchestrationTest, cls).resource_setup()
        cls.build_timeout = CONF.orchestration.build_timeout
        cls.build_interval = CONF.orchestration.build_interval
        cls.stacks = []
        cls.keypairs = []
        cls.images = []

    @classmethod
    def create_stack(cls, stack_name, template_data, parameters=None,
                     environment=None, files=None):
        if parameters is None:
            parameters = {}
        body = cls.client.create_stack(
            stack_name,
            template=template_data,
            parameters=parameters,
            environment=environment,
            files=files)
        stack_id = body.response['location'].split('/')[-1]
        stack_identifier = '%s/%s' % (stack_name, stack_id)
        cls.stacks.append(stack_identifier)
        return stack_identifier

    @classmethod
    def _clear_stacks(cls):
        for stack_identifier in cls.stacks:
            try:
                cls.client.delete_stack(stack_identifier)
            except lib_exc.NotFound:
                pass

        for stack_identifier in cls.stacks:
            try:
                cls.client.wait_for_stack_status(
                    stack_identifier, 'DELETE_COMPLETE')
            except lib_exc.NotFound:
                pass

    @classmethod
    def _create_keypair(cls, name_start='keypair-heat-'):
        kp_name = data_utils.rand_name(name_start)
        body = cls.keypairs_client.create_keypair(name=kp_name)['keypair']
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
    def _create_image(cls, name_start='image-heat-', container_format='bare',
                      disk_format='iso'):
        image_name = data_utils.rand_name(name_start)
        body = cls.images_v2_client.create_image(image_name,
                                                 container_format,
                                                 disk_format)
        image_id = body['id']
        cls.images.append(image_id)
        return body

    @classmethod
    def _clear_images(cls):
        for image_id in cls.images:
            try:
                cls.images_v2_client.delete_image(image_id)
            except lib_exc.NotFound:
                pass

    @classmethod
    def read_template(cls, name, ext='yaml'):
        loc = ["stacks", "templates", "%s.%s" % (name, ext)]
        fullpath = os.path.join(os.path.dirname(__file__), *loc)

        with open(fullpath, "r") as f:
            content = f.read()
            return content

    @classmethod
    def load_template(cls, name, ext='yaml'):
        loc = ["stacks", "templates", "%s.%s" % (name, ext)]
        fullpath = os.path.join(os.path.dirname(__file__), *loc)

        with open(fullpath, "r") as f:
            return yaml.safe_load(f)

    @classmethod
    def resource_cleanup(cls):
        cls._clear_stacks()
        cls._clear_keypairs()
        cls._clear_images()
        super(BaseOrchestrationTest, cls).resource_cleanup()

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
        resources = self.client.list_resources(stack_identifier)['resources']
        self.assertIsInstance(resources, list)
        for res in resources:
            self.assert_fields_in_dict(res, 'logical_resource_id',
                                       'resource_type', 'resource_status',
                                       'updated_time')

        return dict((r['resource_name'], r['resource_type'])
                    for r in resources)

    def get_stack_output(self, stack_identifier, output_key):
        body = self.client.show_stack(stack_identifier)['stack']
        return self.stack_output(body, output_key)
