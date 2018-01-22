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
from tempest.lib.common.utils import data_utils


class BaseKeypairTest(base.BaseV2ComputeTest):
    """Base test case class for all keypair API tests."""

    def _delete_keypair(self, keypair_name, client=None, **params):
        if not client:
            client = self.keypairs_client
        client.delete_keypair(keypair_name, **params)

    def create_keypair(self, keypair_name=None,
                       pub_key=None, keypair_type=None,
                       user_id=None, client=None):
        if not client:
            client = self.keypairs_client
        if keypair_name is None:
            keypair_name = data_utils.rand_name(
                self.__class__.__name__ + '-keypair')
        kwargs = {'name': keypair_name}
        delete_params = {}
        if pub_key:
            kwargs.update({'public_key': pub_key})
        if keypair_type:
            kwargs.update({'type': keypair_type})
        if user_id:
            kwargs.update({'user_id': user_id})
            delete_params['user_id'] = user_id
        body = client.create_keypair(**kwargs)['keypair']
        self.addCleanup(self._delete_keypair, keypair_name,
                        client, **delete_params)
        return body
