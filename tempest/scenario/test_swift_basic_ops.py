# Copyright 2013 IBM Corp.
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


from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestSwiftBasicOps(manager.OfficialClientTest):
    """
    Test swift with the follow operations:
     * get swift stat.
     * create container.
     * upload a file to the created container.
     * list container's objects and assure that the uploaded file is present.
     * delete object from container.
     * list container's objects and assure that the deleted file is gone.
     * delete a container.
     * list containers and assure that the deleted container is gone.
    """

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(TestSwiftBasicOps, cls).setUpClass()
        if not CONF.service_available.swift:
            skip_msg = ("%s skipped as swift is not available" %
                        cls.__name__)
            raise cls.skipException(skip_msg)

    def _get_swift_stat(self):
        """get swift status for our user account."""
        self.object_storage_client.get_account()
        LOG.debug('Swift status information obtained successfully')

    def _create_container(self, container_name=None):
        name = container_name or data_utils.rand_name(
            'swift-scenario-container')
        self.object_storage_client.put_container(name)
        # look for the container to assure it is created
        self._list_and_check_container_objects(name)
        LOG.debug('Container %s created' % (name))
        return name

    def _delete_container(self, container_name):
        self.object_storage_client.delete_container(container_name)
        LOG.debug('Container %s deleted' % (container_name))

    def _upload_object_to_container(self, container_name, obj_name=None):
        obj_name = obj_name or data_utils.rand_name('swift-scenario-object')
        self.object_storage_client.put_object(container_name, obj_name,
                                              data_utils.rand_name('obj_data'),
                                              content_type='text/plain')
        return obj_name

    def _delete_object(self, container_name, filename):
        self.object_storage_client.delete_object(container_name, filename)
        self._list_and_check_container_objects(container_name,
                                               not_present_obj=[filename])

    def _list_and_check_container_objects(self, container_name, present_obj=[],
                                          not_present_obj=[]):
        """
        List objects for a given container and assert which are present and
        which are not.
        """
        meta, response = self.object_storage_client.get_container(
            container_name)
        # create a list with file name only
        object_list = [obj['name'] for obj in response]
        if present_obj:
            for obj in present_obj:
                self.assertIn(obj, object_list)
        if not_present_obj:
            for obj in not_present_obj:
                self.assertNotIn(obj, object_list)

    @test.services('object_storage')
    def test_swift_basic_ops(self):
        self._get_swift_stat()
        container_name = self._create_container()
        obj_name = self._upload_object_to_container(container_name)
        self._list_and_check_container_objects(container_name, [obj_name])
        self._delete_object(container_name, obj_name)
        self._delete_container(container_name)
