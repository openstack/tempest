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

from oslo_log import log as logging

from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestSwiftBasicOps(manager.SwiftScenarioTest):
    """
    Test swift basic ops.
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

    @test.idempotent_id('b920faf1-7b8a-4657-b9fe-9c4512bfb381')
    @test.services('object_storage')
    def test_swift_basic_ops(self):
        self.get_swift_stat()
        container_name = self.create_container()
        obj_name, obj_data = self.upload_object_to_container(container_name)
        self.list_and_check_container_objects(container_name,
                                              present_obj=[obj_name])
        self.download_and_verify(container_name, obj_name, obj_data)
        self.delete_object(container_name, obj_name)
        self.list_and_check_container_objects(container_name,
                                              not_present_obj=[obj_name])
        self.delete_container(container_name)

    @test.idempotent_id('916c7111-cb1f-44b2-816d-8f760e4ea910')
    @test.services('object_storage')
    def test_swift_acl_anonymous_download(self):
        """This test will cover below steps:
        1. Create container
        2. Upload object to the new container
        3. Change the ACL of the container
        4. Check if the object can be download by anonymous user
        5. Delete the object and container
        """
        container_name = self.create_container()
        obj_name, _ = self.upload_object_to_container(container_name)
        obj_url = '%s/%s/%s' % (self.object_client.base_url,
                                container_name, obj_name)
        resp, _ = self.object_client.raw_request(obj_url, 'GET')
        self.assertEqual(resp.status, 401)

        self.change_container_acl(container_name, '.r:*')
        resp, _ = self.object_client.raw_request(obj_url, 'GET')
        self.assertEqual(resp.status, 200)
