# Copyright 2012 OpenStack Foundation
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

from tempest_lib.common.utils import data_utils

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class ImagesTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(ImagesTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if not CONF.compute_feature_enabled.snapshot:
            skip_msg = ("%s skipped as instance snapshotting is not supported"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(ImagesTestJSON, cls).setup_clients()
        cls.client = cls.images_client
        cls.servers_client = cls.servers_client

    @test.attr(type='gate')
    @test.idempotent_id('aa06b52b-2db5-4807-b218-9441f75d74e3')
    def test_delete_saving_image(self):
        snapshot_name = data_utils.rand_name('test-snap')
        server = self.create_test_server(wait_until='ACTIVE')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        image = self.create_image_from_server(server['id'],
                                              name=snapshot_name,
                                              wait_until='SAVING')
        self.client.delete_image(image['id'])
