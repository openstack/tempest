# Copyright 2015 Deutsche Telekom AG
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

from tempest.api.compute import base


class BaseKeypairTest(base.BaseComputeTest):
    """Base test case class for all keypair API tests."""

    _api_version = 2

    @classmethod
    def setup_clients(cls):
        super(BaseKeypairTest, cls).setup_clients()
        cls.client = cls.keypairs_client

    def _delete_keypair(self, keypair_name):
        self.client.delete_keypair(keypair_name)

    def _create_keypair(self, keypair_name, pub_key=None):
        kwargs = {'name': keypair_name}
        if pub_key:
            kwargs.update({'public_key': pub_key})
        body = self.client.create_keypair(**kwargs)['keypair']
        self.addCleanup(self._delete_keypair, keypair_name)
        return body
