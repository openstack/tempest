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

from tempest.common import utils
from tempest.lib import decorators
from tempest.scenario import manager


class TestObjectStorageBasicOps(manager.ObjectStorageScenarioTest):
    @decorators.idempotent_id('b920faf1-7b8a-4657-b9fe-9c4512bfb381')
    @utils.services('object_storage')
    def test_swift_basic_ops(self):
        """Test swift basic ops.

        * get swift stat.
        * create container.
        * upload a file to the created container.
        * list container's objects and assure that the uploaded file is
          present.
        * download the object and check the content
        * delete object from container.
        * list container's objects and assure that the deleted file is gone.
        * delete a container.
        """
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

    @decorators.idempotent_id('916c7111-cb1f-44b2-816d-8f760e4ea910')
    @decorators.attr(type='slow')
    @utils.services('object_storage')
    def test_swift_acl_anonymous_download(self):
        """This test will cover below steps:

        1. Create container
        2. Upload object to the new container
        3. Change the ACL of the container
        4. Check if the object can be download by anonymous user
        5. Delete the object and container
        """
        container_name = self.create_container()
        obj_name, obj_data = self.upload_object_to_container(container_name)
        obj_url = '%s/%s/%s' % (self.object_client.base_url,
                                container_name, obj_name)
        resp, _ = self.object_client.raw_request(obj_url, 'GET')
        self.assertEqual(resp.status, 401)
        metadata_param = {'X-Container-Read': '.r:*'}
        self.container_client.create_update_or_delete_container_metadata(
            container_name, create_update_metadata=metadata_param,
            create_update_metadata_prefix='')
        resp, _ = self.container_client.list_container_metadata(container_name)
        self.assertEqual(metadata_param['X-Container-Read'],
                         resp['x-container-read'])
        resp, data = self.object_client.raw_request(obj_url, 'GET')
        self.assertEqual(resp.status, 200)
        self.assertEqual(obj_data, data)
