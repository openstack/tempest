# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp.
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

import cStringIO as StringIO

from tempest import clients
from tempest.common import isolated_creds
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.openstack.common import log as logging
import tempest.test

LOG = logging.getLogger(__name__)


class BaseImageTest(tempest.test.BaseTestCase):
    """Base test class for Image API tests."""

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(BaseImageTest, cls).setUpClass()
        cls.created_images = []
        cls._interface = 'json'
        cls.isolated_creds = isolated_creds.IsolatedCreds(
            cls.__name__, network_resources=cls.network_resources)
        if not cls.config.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if cls.config.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_primary_creds()
            username, tenant_name, password = creds
            cls.os = clients.Manager(username=username,
                                     password=password,
                                     tenant_name=tenant_name)
        else:
            cls.os = clients.Manager()

    @classmethod
    def tearDownClass(cls):
        for image_id in cls.created_images:
            try:
                cls.client.delete_image(image_id)
            except exceptions.NotFound:
                pass

        for image_id in cls.created_images:
                cls.client.wait_for_resource_deletion(image_id)
        cls.isolated_creds.clear_isolated_creds()
        super(BaseImageTest, cls).tearDownClass()

    @classmethod
    def create_image(cls, **kwargs):
        """Wrapper that returns a test image."""
        name = data_utils.rand_name(cls.__name__ + "-instance")

        if 'name' in kwargs:
            name = kwargs.pop('name')

        container_format = kwargs.pop('container_format')
        disk_format = kwargs.pop('disk_format')

        resp, image = cls.client.create_image(name, container_format,
                                              disk_format, **kwargs)
        cls.created_images.append(image['id'])
        return resp, image


class BaseV1ImageTest(BaseImageTest):

    @classmethod
    def setUpClass(cls):
        super(BaseV1ImageTest, cls).setUpClass()
        cls.client = cls.os.image_client
        if not cls.config.image_feature_enabled.api_v1:
            msg = "Glance API v1 not supported"
            raise cls.skipException(msg)


class BaseV1ImageMembersTest(BaseV1ImageTest):
    @classmethod
    def setUpClass(cls):
        super(BaseV1ImageMembersTest, cls).setUpClass()
        if cls.config.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_alt_creds()
            username, tenant_name, password = creds
            cls.os_alt = clients.Manager(username=username,
                                         password=password,
                                         tenant_name=tenant_name)
            cls.alt_tenant_id = cls.isolated_creds.get_alt_tenant()['id']
        else:
            cls.os_alt = clients.AltManager()
            identity_client = cls._get_identity_admin_client()
            cls.alt_tenant_id = identity_client.get_tenant_by_name(
                cls.os_alt.tenant_name)['id']

        cls.alt_img_cli = cls.os_alt.image_client

    def _create_image(self):
        image_file = StringIO.StringIO('*' * 1024)
        resp, image = self.create_image(container_format='bare',
                                        disk_format='raw',
                                        is_public=False,
                                        data=image_file)
        self.assertEqual(201, resp.status)
        image_id = image['id']
        return image_id


class BaseV2ImageTest(BaseImageTest):

    @classmethod
    def setUpClass(cls):
        super(BaseV2ImageTest, cls).setUpClass()
        cls.client = cls.os.image_client_v2
        if not cls.config.image_feature_enabled.api_v2:
            msg = "Glance API v2 not supported"
            raise cls.skipException(msg)


class BaseV2MemeberImageTest(BaseImageTest):

    @classmethod
    def setUpClass(cls):
        super(BaseV2MemeberImageTest, cls).setUpClass()
        if cls.config.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_alt_creds()
            username, tenant_name, password = creds
            cls.os_alt = clients.Manager(username=username,
                                         password=password,
                                         tenant_name=tenant_name,
                                         interface=cls._interface)
            cls.alt_tenant_id = cls.isolated_creds.get_alt_tenant()['id']
        else:
            cls.os_alt = clients.AltManager()
            alt_tenant_name = cls.os_alt.tenant_name
            identity_client = cls._get_identity_admin_client()
            cls.alt_tenant_id = identity_client.get_tenant_by_name(
                alt_tenant_name)['id']
        cls.os_img_client = cls.os.image_client_v2
        cls.alt_img_client = cls.os_alt.image_client_v2

    def _list_image_ids_as_alt(self):
        _, image_list = self.alt_img_client.image_list()
        image_ids = map(lambda x: x['id'], image_list)
        return image_ids

    def _create_image(self):
        name = data_utils.rand_name('image')
        resp, image = self.os_img_client.create_image(name,
                                                      container_format='bare',
                                                      disk_format='raw')
        image_id = image['id']
        self.addCleanup(self.os_img_client.delete_image, image_id)
        return image_id
