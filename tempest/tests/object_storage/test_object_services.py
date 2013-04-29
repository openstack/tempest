# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from tempest.common.utils.data_utils import arbitrary_string
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr
from tempest.tests.object_storage import base
import testtools
import time


class ObjectTest(base.BaseObjectTest):

    @classmethod
    def setUpClass(cls):
        super(ObjectTest, cls).setUpClass()

        #Create a container
        cls.container_name = rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)

        # Randomly creating user
        cls.data.setup_test_user()

        resp, body = cls.token_client.auth(cls.data.test_user,
                                           cls.data.test_password,
                                           cls.data.test_tenant)
        cls.new_token = cls.token_client.get_token(cls.data.test_user,
                                                   cls.data.test_password,
                                                   cls.data.test_tenant)

        cls.custom_headers = {'X-Auth-Token': cls.new_token}

    @classmethod
    def tearDownClass(cls):
        #Get list of all object in the container
        objlist = cls.container_client.list_all_container_objects(
            cls.container_name)

        #Attempt to delete every object in the container
        for obj in objlist:
            resp, _ = cls.object_client.delete_object(cls.container_name,
                                                      obj['name'])

        #Attempt to delete the container
        resp, _ = cls.container_client.delete_container(cls.container_name)

        #Attempt to the delete the user setup created
        cls.data.teardown_all()

    @attr(type='smoke')
    def test_create_object(self):
        # Create storage object, test response

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        #Create another Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertEqual(resp['status'], '201')

    @attr(type='smoke')
    def test_delete_object(self):
        # Create and delete a storage object, test responses

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        resp, _ = self.object_client.delete_object(self.container_name,
                                                   object_name)
        self.assertEqual(resp['status'], '204')

    @attr(type='smoke')
    def test_object_metadata(self):
        # Add metadata to storage object, test if metadata is retrievable

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        #Set Object Metadata
        meta_key = rand_name(name='test-')
        meta_value = rand_name(name='MetaValue-')
        orig_metadata = {meta_key: meta_value}

        resp, _ = self.object_client.update_object_metadata(
            self.container_name, object_name,
            orig_metadata)
        self.assertEqual(resp['status'], '202')

        #Get Object Metadata
        resp, resp_metadata = self.object_client.list_object_metadata(
            self.container_name, object_name)

        self.assertEqual(resp['status'], '200')
        actual_meta_key = 'x-object-meta-' + meta_key
        self.assertTrue(actual_meta_key in resp)
        self.assertEqual(resp[actual_meta_key], meta_value)

    @attr(type='smoke')
    def test_get_object(self):
        # Retrieve object's data(in response body)

        #Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        resp, body = self.object_client.get_object(self.container_name,
                                                   object_name)
        self.assertEqual(resp['status'], '200')
        # Check data
        self.assertEqual(body, data)

    @attr(type='smoke')
    def test_copy_object_in_same_container(self):
        # Copy storage object

        # Create source Object
        src_object_name = rand_name(name='SrcObject')
        src_data = arbitrary_string(size=len(src_object_name) * 2,
                                    base_text=src_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   src_object_name, src_data)

        # Create destination Object
        dst_object_name = rand_name(name='DstObject')
        dst_data = arbitrary_string(size=len(dst_object_name) * 3,
                                    base_text=dst_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   dst_object_name, dst_data)

        # Copy source object to destination
        resp, _ = self.object_client.copy_object_in_same_container(
            self.container_name, src_object_name, dst_object_name)
        self.assertEqual(resp['status'], '201')

        # Check data
        resp, body = self.object_client.get_object(self.container_name,
                                                   dst_object_name)
        self.assertEqual(body, src_data)

    @attr(type='smoke')
    def test_copy_object_to_itself(self):
        # Change the content type of an existing object

        # Create Object
        object_name = rand_name(name='TestObject')
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        # Get the old content type
        resp_tmp, _ = self.object_client.list_object_metadata(
            self.container_name,
            object_name)
        # Change the content type of the object
        metadata = {'content-type': 'text/plain; charset=UTF-8'}
        self.assertNotEqual(resp_tmp['content-type'], metadata['content-type'])
        resp, _ = self.object_client.copy_object_in_same_container(
            self.container_name, object_name, object_name, metadata)
        self.assertEqual(resp['status'], '201')

        # Check the content type
        resp, _ = self.object_client.list_object_metadata(self.container_name,
                                                          object_name)
        self.assertEqual(resp['content-type'], metadata['content-type'])

    @attr(type='smoke')
    def test_copy_object_2d_way(self):
        # Copy storage object

        # Create source Object
        src_object_name = rand_name(name='SrcObject')
        src_data = arbitrary_string(size=len(src_object_name) * 2,
                                    base_text=src_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   src_object_name, src_data)

        # Create destination Object
        dst_object_name = rand_name(name='DstObject')
        dst_data = arbitrary_string(size=len(dst_object_name) * 3,
                                    base_text=dst_object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   dst_object_name, dst_data)

        # Copy source object to destination
        resp, _ = self.object_client.copy_object_2d_way(self.container_name,
                                                        src_object_name,
                                                        dst_object_name)
        self.assertEqual(resp['status'], '201')

        # Check data
        resp, body = self.object_client.get_object(self.container_name,
                                                   dst_object_name)
        self.assertEqual(body, src_data)

    @attr(type='smoke')
    def test_copy_object_across_containers(self):
        # Copy storage object across containers

        #Create a container so as to use as source container
        src_container_name = rand_name(name='TestSourceContainer')
        self.container_client.create_container(src_container_name)

        #Create a container so as to use as destination container
        dst_container_name = rand_name(name='TestDestinationContainer')
        self.container_client.create_container(dst_container_name)

        # Create Object in source container
        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name) * 2,
                                base_text=object_name)
        resp, _ = self.object_client.create_object(src_container_name,
                                                   object_name, data)
        #Set Object Metadata
        meta_key = rand_name(name='test-')
        meta_value = rand_name(name='MetaValue-')
        orig_metadata = {meta_key: meta_value}

        resp, _ = self.object_client.update_object_metadata(src_container_name,
                                                            object_name,
                                                            orig_metadata)
        self.assertEqual(resp['status'], '202')

        try:
            # Copy object from source container to destination container
            resp, _ = self.object_client.copy_object_across_containers(
                src_container_name, object_name, dst_container_name,
                object_name)
            self.assertEqual(resp['status'], '201')

            # Check if object is present in destination container
            resp, body = self.object_client.get_object(dst_container_name,
                                                       object_name)
            self.assertEqual(body, data)
            actual_meta_key = 'x-object-meta-' + meta_key
            self.assertTrue(actual_meta_key in resp)
            self.assertEqual(resp[actual_meta_key], meta_value)

        except Exception as e:
            self.fail("Got exception :%s ; while copying"
                      " object across containers" % e)
        finally:
            #Delete objects from respective containers
            resp, _ = self.object_client.delete_object(dst_container_name,
                                                       object_name)
            resp, _ = self.object_client.delete_object(src_container_name,
                                                       object_name)
            #Delete containers created in this method
            resp, _ = self.container_client.delete_container(
                src_container_name)
            resp, _ = self.container_client.delete_container(
                dst_container_name)

    @attr(type='smoke')
    def test_access_public_container_object_without_using_creds(self):
        # Make container public-readable, and access the object
           # anonymously, e.g. without using credentials

        try:
            resp_meta = None
            # Update Container Metadata to make public readable
            cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
            resp_meta, body = self.container_client.update_container_metadata(
                self.container_name, metadata=cont_headers,
                metadata_prefix='')
            self.assertEqual(resp_meta['status'], '204')

            # Create Object
            object_name = rand_name(name='Object')
            data = arbitrary_string(size=len(object_name),
                                    base_text=object_name)
            resp, _ = self.object_client.create_object(self.container_name,
                                                       object_name, data)
            self.assertEqual(resp['status'], '201')

            # List container metadata
            resp_meta, _ = self.container_client.list_container_metadata(
                self.container_name)
            self.assertEqual(resp_meta['status'], '204')
            self.assertIn('x-container-read', resp_meta)
            self.assertEqual(resp_meta['x-container-read'], '.r:*,.rlistings')

            # Trying to Get Object with empty Headers as it is public readable
            resp, body = self.custom_object_client.get_object(
                self.container_name, object_name,
                metadata={})
            self.assertEqual(body, data)
        finally:
            if resp_meta['status'] == '204':
                # Delete updated container metadata, to revert back.
                resp, body = self.container_client.delete_container_metadata(
                    self.container_name, metadata=cont_headers,
                    metadata_prefix='')

                resp, _ = self.container_client.list_container_metadata(
                    self.container_name)
                self.assertEqual(resp['status'], '204')
                self.assertIn('x-container-read', resp)
                self.assertEqual(resp['x-container-read'], 'x')

    @attr(type='smoke')
    def test_access_public_object_with_another_user_creds(self):
        #Make container public-readable, and access the object
            #anonymously, e.g. using another user credentials

        try:
            resp_meta = None
            cont_headers = {'X-Container-Read': '.r:*,.rlistings'}
            resp_meta, body = self.container_client.update_container_metadata(
                self.container_name, metadata=cont_headers,
                metadata_prefix='')
            self.assertEqual(resp_meta['status'], '204')
            # Create Object
            object_name = rand_name(name='Object')
            data = arbitrary_string(size=len(object_name) * 1,
                                    base_text=object_name)
            resp, _ = self.object_client.create_object(self.container_name,
                                                       object_name, data)
            self.assertEqual(resp['status'], '201')

            # List container metadata
            resp, _ = self.container_client.list_container_metadata(
                self.container_name)
            self.assertEqual(resp['status'], '204')
            self.assertIn('x-container-read', resp)
            self.assertEqual(resp['x-container-read'], '.r:*,.rlistings')

            # Trying to GET Auth Token of Alternate user
            token = self.identity_client_alt.get_auth()
            headers = {'X-Auth-Token': token}

            # Trying to create object with Alternate user creds
            resp, body = self.custom_object_client.get_object(
                self.container_name, object_name,
                metadata=headers)
            self.assertEqual(body, data)

        except Exception as e:
            self.fail("Failed to get public readable object with another"
                      " user creds raised exception is %s" % e)

        finally:
            if resp_meta['status'] == '204':
                # Delete updated container metadata, to revert back.
                resp, body = self.container_client.delete_container_metadata(
                    self.container_name, metadata=cont_headers,
                    metadata_prefix='')

                resp, _ = self.container_client.list_container_metadata(
                    self.container_name)
                self.assertEqual(resp['status'], '204')
                self.assertIn('x-container-read', resp)
                self.assertEqual(resp['x-container-read'], 'x')

    @testtools.skip('Until Bug #1020722 is resolved.')
    @attr(type='smoke')
    def test_write_public_object_without_using_creds(self):
        #Make container public-writable, and create object
            #anonymously, e.g. without using credentials
        try:
            resp_meta = None
            # Update Container Metadata to make public readable
            cont_headers = {'X-Container-Write': '-*'}
            resp_meta, body = self.container_client.update_container_metadata(
                self.container_name, metadata=cont_headers,
                metadata_prefix='')
            self.assertEqual(resp_meta['status'], '204')
            # List container metadata
            resp, _ = self.container_client.list_container_metadata(
                self.container_name)

            self.assertEqual(resp['status'], '204')
            self.assertIn('x-container-write', resp)
            self.assertEqual(resp['x-container-write'], '-*')

            object_name = rand_name(name='Object')
            data = arbitrary_string(size=len(object_name),
                                    base_text=object_name)

            headers = {'Content-Type': 'application/json',
                       'Accept': 'application/json'}

            #Trying to Create object without using creds
            resp, body = self.custom_object_client.create_object(
                self.container_name, object_name,
                data, metadata=headers)
            self.assertEqual(resp['status'], '201')

        except Exception as e:
            self.fail("Failed to create public writable object without using"
                      " creds raised exception is %s" % e)

        finally:
            if resp_meta['status'] == '204':
                # Delete updated container metadata, to revert back.
                resp, body = self.container_client.delete_container_metadata(
                    self.container_name, metadata=cont_headers,
                    metadata_prefix='')

                resp, _ = self.container_client.list_container_metadata(
                    self.container_name)
                self.assertEqual(resp['status'], '204')
                self.assertIn('x-container-write', resp)
                self.assertEqual(resp['x-container-write'], 'x')

    @testtools.skip('Until Bug #1020722 is resolved.')
    @attr(type='smoke')
    def test_write_public_with_another_user_creds(self):
        #Make container public-writable, and create object
            #anonymously, e.g. with another user credentials

        try:
            resp_meta = None
            # Update Container Metadata to make public readable
            cont_headers = {'X-Container-Write': '-*'}
            resp_meta, body = self.container_client.update_container_metadata(
                self.container_name, metadata=cont_headers,
                metadata_prefix='')
            self.assertEqual(resp_meta['status'], '204')
            # List container metadata
            resp, _ = self.container_client.list_container_metadata(
                self.container_name)

            self.assertEqual(resp['status'], '204')
            self.assertIn('x-container-write', resp)
            self.assertEqual(resp['x-container-write'], '-*')

            #Trying to GET auth token of Alternate user
            token = self.identity_client_alt.get_auth()

            headers = {'Content-Type': 'application/json',
                       'Accept': 'application/json',
                       'X-Auth-Token': token}

            #Trying to Create an object with another user creds
            object_name = rand_name(name='Object')
            data = arbitrary_string(size=len(object_name),
                                    base_text=object_name)
            resp, body = self.custom_object_client.create_object(
                self.container_name, object_name,
                data, metadata=headers)
            self.assertEqual(resp['status'], '201')

        except Exception as e:
            self.fail("Failed to create public writable object with another"
                      " user creds raised exception is %s" % e)

        finally:
            if resp_meta['status'] == '204':
                # Delete updated container metadata, to revert back.
                resp, body = self.container_client.delete_container_metadata(
                    self.container_name, metadata=cont_headers,
                    metadata_prefix='')

                resp, _ = self.container_client.list_container_metadata(
                    self.container_name)
                self.assertEqual(resp['status'], '204')
                self.assertIn('x-container-write', resp)
                self.assertEqual(resp['x-container-write'], 'x')

    @attr(type='negative')
    def test_access_object_without_using_creds(self):
        # Attempt to access the object anonymously, e.g.
            # not using any credentials

        # Create Object
        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name),
                                base_text=object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)
        self.assertEqual(resp['status'], '201')

        # Trying to Get Object with empty Headers
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.get_object,
                          self.container_name, object_name, metadata={})

    @attr(type='negative')
    def test_write_object_without_using_creds(self):
        # Attempt to write to the object anonymously, e.g.
        # not using any credentials

        # Trying to Create Object with empty Headers
        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name),
                                base_text=object_name)
        obj_headers = {'Content-Type': 'application/json',
                       'Accept': 'application/json'}

        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.create_object,
                          self.container_name, object_name, data,
                          metadata=obj_headers)

    @attr(type='negative')
    def test_delete_object_without_using_creds(self):
        # Attempt to delete the object anonymously,
            # e.g. not using any credentials

        # Create Object
        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name),
                                base_text=object_name)
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        # Trying to Delete Object with empty Headers
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.delete_object,
                          self.container_name, object_name)

    @attr(type='negative')
    def test_write_object_with_non_authorized_user(self):
        #Attempt to upload another file using non authorized user

        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name) * 5,
                                base_text=object_name)

        # Trying to Create Object with non authorized user token
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.create_object,
                          self.container_name, object_name, data,
                          metadata=self.custom_headers)

    @attr(type='negative')
    def test_read_object_with_non_authorized_user(self):
        #Attempt to download the file using non authorized user

        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name) * 5,
                                base_text=object_name)

        resp, body = self.object_client.create_object(
            self.container_name, object_name,
            data)
        self.assertEqual(resp['status'], '201')

        # Trying to Get Object with non authorized user token
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.get_object,
                          self.container_name, object_name,
                          metadata=self.custom_headers)

    @attr(type='negative')
    def test_delete_object_with_non_authorized_user(self):
        #Attempt to delete container using non authorized user

        object_name = rand_name(name='Object')
        data = arbitrary_string(size=len(object_name) * 5,
                                base_text=object_name)

        resp, body = self.object_client.create_object(
            self.container_name, object_name,
            data)
        self.assertEqual(resp['status'], '201')

        # Trying to Delete Object with non authorized user token
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_object_client.delete_object,
                          self.container_name, object_name,
                          metadata=self.custom_headers)

    @testtools.skip('Until Bug #1097137 is resolved.')
    @attr(type='positive')
    def test_get_object_using_temp_url(self):
        #Access object using temp url within expiry time

        try:
            #Update Account Metadata
            # Flag to check if account metadata got updated
            flag = False
            key = 'Meta'
            metadata = {'Temp-URL-Key': key}
            resp, _ = self.account_client.create_account_metadata(
                metadata=metadata)
            self.assertEqual(resp['status'], '204')
            flag = True

            resp, _ = self.account_client.list_account_metadata()
            self.assertIn('x-account-meta-temp-url-key', resp)
            self.assertEqual(resp['x-account-meta-temp-url-key'], key)

            # Create Object
            object_name = rand_name(name='ObjectTemp')
            data = arbitrary_string(size=len(object_name),
                                    base_text=object_name)
            self.object_client.create_object(self.container_name,
                                             object_name, data)

            expires = int(time.time() + 10)

            #Trying to GET object using temp URL with in expiry time
            _, body = self.object_client.get_object_using_temp_url(
                self.container_name, object_name,
                expires, key)

            self.assertEqual(body, data)

        finally:
            if flag:
                resp, _ = self.account_client.delete_account_metadata(
                    metadata=metadata)
                resp, _ = self.account_client.list_account_metadata()
                self.assertNotIn('x-account-meta-temp-url-key', resp)

    @attr(type='positive')
    def test_object_upload_in_segments(self):
        #Attempt to upload object in segments

        #Create Object
        object_name = rand_name(name='LObject')
        data = arbitrary_string(size=len(object_name),
                                base_text=object_name)
        segments = 10
        self.object_client.create_object(self.container_name,
                                         object_name, data)
        #Uploading 10 segments
        for i in range(segments):
            resp, _ = self.object_client.create_object_segments(
                self.container_name, object_name,
                i, data)
        # Creating a Manifest File (Metadata Update)

        metadata = {'X-Object-Manifest': '%s/%s/'
                    % (self.container_name, object_name)}
        resp, _ = self.object_client.update_object_metadata(
            self.container_name, object_name,
            metadata, metadata_prefix='')
        resp, _ = self.object_client.list_object_metadata(
            self.container_name, object_name)
        self.assertIn('x-object-manifest', resp)
        self.assertEqual(resp['x-object-manifest'],
                         '%s/%s/' % (self.container_name, object_name))

        #Downloading the object
        resp, body = self.object_client.get_object(
            self.container_name, object_name)

        self.assertEqual(data * segments, body)
