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

from six import moves

from tempest.common import image as common_image
from tempest.common.utils import data_utils
from tempest import config
from tempest.lib.common.utils import test_utils
import tempest.test

CONF = config.CONF


class BaseImageTest(tempest.test.BaseTestCase):
    """Base test class for Image API tests."""

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseImageTest, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseImageTest, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(BaseImageTest, cls).resource_setup()
        cls.created_images = []

    @classmethod
    def resource_cleanup(cls):
        for image_id in cls.created_images:
            test_utils.call_and_ignore_notfound_exc(
                cls.client.delete_image, image_id)

        for image_id in cls.created_images:
                cls.client.wait_for_resource_deletion(image_id)
        super(BaseImageTest, cls).resource_cleanup()

    @classmethod
    def create_image(cls, data=None, **kwargs):
        """Wrapper that returns a test image."""

        if 'name' not in kwargs:
            name = data_utils.rand_name(cls.__name__ + "-instance")
            kwargs['name'] = name

        params = cls._get_create_params(**kwargs)
        if data:
            # NOTE: On glance v1 API, the data should be passed on
            # a header. Then here handles the data separately.
            params['data'] = data

        image = cls.client.create_image(**params)
        # Image objects returned by the v1 client have the image
        # data inside a dict that is keyed against 'image'.
        if 'image' in image:
            image = image['image']
        cls.created_images.append(image['id'])
        return image

    @classmethod
    def _get_create_params(cls, **kwargs):
        return kwargs


class BaseV1ImageTest(BaseImageTest):

    @classmethod
    def skip_checks(cls):
        super(BaseV1ImageTest, cls).skip_checks()
        if not CONF.image_feature_enabled.api_v1:
            msg = "Glance API v1 not supported"
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(BaseV1ImageTest, cls).setup_clients()
        cls.client = cls.os.image_client

    @classmethod
    def _get_create_params(cls, **kwargs):
        return {'headers': common_image.image_meta_to_headers(**kwargs)}


class BaseV1ImageMembersTest(BaseV1ImageTest):

    credentials = ['primary', 'alt']

    @classmethod
    def setup_clients(cls):
        super(BaseV1ImageMembersTest, cls).setup_clients()
        cls.image_member_client = cls.os.image_member_client
        cls.alt_image_member_client = cls.os_alt.image_member_client
        cls.alt_img_cli = cls.os_alt.image_client

    @classmethod
    def resource_setup(cls):
        super(BaseV1ImageMembersTest, cls).resource_setup()
        cls.alt_tenant_id = cls.alt_image_member_client.tenant_id

    def _create_image(self):
        image_file = moves.cStringIO(data_utils.random_bytes())
        image = self.create_image(container_format='bare',
                                  disk_format='raw',
                                  is_public=False,
                                  data=image_file)
        image_id = image['id']
        return image_id


class BaseV2ImageTest(BaseImageTest):

    @classmethod
    def skip_checks(cls):
        super(BaseV2ImageTest, cls).skip_checks()
        if not CONF.image_feature_enabled.api_v2:
            msg = "Glance API v2 not supported"
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(BaseV2ImageTest, cls).setup_clients()
        cls.client = cls.os.image_client_v2
        cls.namespaces_client = cls.os.namespaces_client
        cls.resource_types_client = cls.os.resource_types_client
        cls.schemas_client = cls.os.schemas_client


class BaseV2MemberImageTest(BaseV2ImageTest):

    credentials = ['primary', 'alt']

    @classmethod
    def setup_clients(cls):
        super(BaseV2MemberImageTest, cls).setup_clients()
        cls.image_member_client = cls.os.image_member_client_v2
        cls.alt_image_member_client = cls.os_alt.image_member_client_v2
        cls.alt_img_client = cls.os_alt.image_client_v2

    @classmethod
    def resource_setup(cls):
        super(BaseV2MemberImageTest, cls).resource_setup()
        cls.alt_tenant_id = cls.alt_image_member_client.tenant_id

    def _list_image_ids_as_alt(self):
        image_list = self.alt_img_client.list_images()['images']
        image_ids = map(lambda x: x['id'], image_list)
        return image_ids

    def _create_image(self):
        name = data_utils.rand_name('image')
        image = self.client.create_image(name=name,
                                         container_format='bare',
                                         disk_format='raw')
        image_id = image['id']
        self.addCleanup(self.client.delete_image, image_id)
        return image_id


class BaseV1ImageAdminTest(BaseImageTest):
    credentials = ['admin', 'primary']

    @classmethod
    def setup_clients(cls):
        super(BaseV1ImageAdminTest, cls).setup_clients()
        cls.client = cls.os.image_client
        cls.admin_client = cls.os_adm.image_client


class BaseV2ImageAdminTest(BaseImageTest):
    credentials = ['admin', 'primary']

    @classmethod
    def setup_clients(cls):
        super(BaseV2ImageAdminTest, cls).setup_clients()
        cls.client = cls.os.image_client_v2
        cls.admin_client = cls.os_adm.image_client_v2
