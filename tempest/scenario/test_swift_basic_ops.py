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

from tempest.common import http
from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestSwiftBasicOps(manager.ScenarioTest):
    """
    Test swift with the follow operations:
     * get swift stat.
     * create container.
     * upload a file to the created container.
     * list container's objects and assure that the uploaded file is present.
     * download the object and check the content
     * delete object from container.
     * list container's objects and assure that the deleted file is gone.
     * delete a container.
     * list containers and assure that the deleted container is gone.
     * change ACL of the container and make sure it works successfully
    """

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(TestSwiftBasicOps, cls).setUpClass()
        if not CONF.service_available.swift:
            skip_msg = ("%s skipped as swift is not available" %
                        cls.__name__)
            raise cls.skipException(skip_msg)
        # Clients for Swift
        cls.account_client = cls.manager.account_client
        cls.container_client = cls.manager.container_client
        cls.object_client = cls.manager.object_client

    def _get_swift_stat(self):
        """get swift status for our user account."""
        self.account_client.list_account_containers()
        LOG.debug('Swift status information obtained successfully')

    def _create_container(self, container_name=None):
        name = container_name or data_utils.rand_name(
            'swift-scenario-container')
        self.container_client.create_container(name)
        # look for the container to assure it is created
        self._list_and_check_container_objects(name)
        LOG.debug('Container %s created' % (name))
        return name

    def _delete_container(self, container_name):
        self.container_client.delete_container(container_name)
        LOG.debug('Container %s deleted' % (container_name))

    def _upload_object_to_container(self, container_name, obj_name=None):
        obj_name = obj_name or data_utils.rand_name('swift-scenario-object')
        obj_data = data_utils.arbitrary_string()
        self.object_client.create_object(container_name, obj_name, obj_data)
        return obj_name, obj_data

    def _delete_object(self, container_name, filename):
        self.object_client.delete_object(container_name, filename)
        self._list_and_check_container_objects(container_name,
                                               not_present_obj=[filename])

    def _list_and_check_container_objects(self, container_name, present_obj=[],
                                          not_present_obj=[]):
        """
        List objects for a given container and assert which are present and
        which are not.
        """
        _, object_list = self.container_client.list_container_contents(
            container_name)
        if present_obj:
            for obj in present_obj:
                self.assertIn(obj, object_list)
        if not_present_obj:
            for obj in not_present_obj:
                self.assertNotIn(obj, object_list)

    def _change_container_acl(self, container_name, acl):
        metadata_param = {'metadata_prefix': 'x-container-',
                          'metadata': {'read': acl}}
        self.container_client.update_container_metadata(container_name,
                                                        **metadata_param)
        resp, _ = self.container_client.list_container_metadata(container_name)
        self.assertEqual(resp['x-container-read'], acl)

    def _download_and_verify(self, container_name, obj_name, expected_data):
        _, obj = self.object_client.get_object(container_name, obj_name)
        self.assertEqual(obj, expected_data)

    @test.services('object_storage')
    def test_swift_basic_ops(self):
        self._get_swift_stat()
        container_name = self._create_container()
        obj_name, obj_data = self._upload_object_to_container(container_name)
        self._list_and_check_container_objects(container_name, [obj_name])
        self._download_and_verify(container_name, obj_name, obj_data)
        self._delete_object(container_name, obj_name)
        self._delete_container(container_name)

    @test.services('object_storage')
    def test_swift_acl_anonymous_download(self):
        """This test will cover below steps:
        1. Create container
        2. Upload object to the new container
        3. Change the ACL of the container
        4. Check if the object can be download by anonymous user
        5. Delete the object and container
        """
        container_name = self._create_container()
        obj_name, _ = self._upload_object_to_container(container_name)
        obj_url = '%s/%s/%s' % (self.object_client.base_url,
                                container_name, obj_name)
        http_client = http.ClosingHttp()
        resp, _ = http_client.request(obj_url, 'GET')
        self.assertEqual(resp.status, 401)
        self._change_container_acl(container_name, '.r:*')
        resp, _ = http_client.request(obj_url, 'GET')
        self.assertEqual(resp.status, 200)
        self._delete_object(container_name, obj_name)
        self._delete_container(container_name)
