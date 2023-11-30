# Copyright 2023 Red Hat, Inc.
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

from tempest.api.image import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ImageTaskCreate(base.BaseV2ImageAdminTest):
    """Test image task operations"""

    @classmethod
    def skip_checks(cls):
        # TODO(msava): Add additional skipcheck with task conversion_format and
        # glance ceph backend then will be available
        # in tempest image service config options.
        super(ImageTaskCreate, cls).skip_checks()
        if not CONF.image.http_image:
            skip_msg = ("%s skipped as http_image is not available " %
                        cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def resource_setup(cls):
        super(ImageTaskCreate, cls).resource_setup()

    @staticmethod
    def _prepare_image_tasks_param(type="import",
                                   disk_format=['qcow2'],
                                   image_from_format=['qcow2'],
                                   image_location=CONF.image.http_image):
        # TODO(msava): Need to add additional disk formats then
        # task conversion_format and glance Ceph backend will be
        # available in image service options
        """Prepare image task params.
        By default, will create task type 'import'

        The same index is used for both params and creates a task
        :param type Type of the task.
        :param disk_format: Each format in the list is a different task.
        :param image_from_format: Each format in the list is a different task.
        :param image_location Location to import image from.
        :return: A list with all task.
        """
        i = 0
        tasks = list()
        while i < len(disk_format):
            image_name = data_utils.rand_name(
                prefix=CONF.resource_name_prefix, name="task_image")
            image_property = {"container_format": "bare",
                              "disk_format": disk_format[0],
                              "visibility": "public",
                              "name": image_name
                              }
            task = {
                "type": type,
                "input": {
                    "image_properties": image_property,
                    "import_from_format": image_from_format[0],
                    "import_from": image_location
                }
            }
            tasks.append(task)
            i += 1
        return tasks

    def _verify_disk_format(self, task_body):
        expected_disk_format = \
            task_body['input']['image_properties']['disk_format']
        image_id = task_body['result']['image_id']
        observed_disk_format = self.admin_client.show_image(
            image_id)['disk_format']
        # If glance backend storage is Ceph glance will convert
        # image to raw format.
        # TODO(msava): Need to change next lines once task conversion_format
        # and glance ceph backend will be available in image service options
        if observed_disk_format == 'raw':
            return
        self.assertEqual(observed_disk_format, expected_disk_format,
                         message="Expected disk format not match ")

    @decorators.skip_because(bug='2030527')
    @decorators.idempotent_id('669d5387-0340-4abf-b62d-7cc89f539c8c')
    def test_image_tasks_create(self):
        """Test task type 'import' image """

        # Prepare params for task type 'import'
        tasks = self._prepare_image_tasks_param()

        # Create task type 'import'
        body = self.os_admin.tasks_client.create_task(**tasks[0])
        task_id = body['id']
        task_body = waiters.wait_for_tasks_status(self.os_admin.tasks_client,
                                                  task_id, 'success')
        self.addCleanup(self.admin_client.delete_image,
                        task_body['result']['image_id'])
        task_image_id = task_body['result']['image_id']
        waiters.wait_for_image_status(self.client, task_image_id, 'active')
        self._verify_disk_format(task_body)

        # Verify disk format
        image_body = self.client.show_image(task_image_id)
        task_disk_format = \
            task_body['input']['image_properties']['disk_format']
        image_disk_format = image_body['disk_format']
        self.assertEqual(
            image_disk_format, task_disk_format,
            message="Image Disc format %s not match to expected %s"
                    % (image_disk_format, task_disk_format))

    @decorators.idempotent_id("ad6450c6-7060-4ee7-a2d1-41c2604b446c")
    @decorators.attr(type=['negative'])
    def test_task_create_fake_image_location(self):
        kwargs = {
            'prefix': CONF.resource_name_prefix,
            'name': 'dummy-img-file'
        }
        http_fake_url = ''.join(
            ["http://", data_utils.rand_name(**kwargs), ".qcow2"])
        task = self._prepare_image_tasks_param(
            image_from_format=['qcow2'],
            disk_format=['qcow2'],
            image_location=http_fake_url)
        body = self.os_admin.tasks_client.create_task(**task[0])
        task_observed = \
            waiters.wait_for_tasks_status(self.os_admin.tasks_client,
                                          body['id'], 'failure')
        task_observed = task_observed['status']
        self.assertEqual(task_observed, 'failure')
