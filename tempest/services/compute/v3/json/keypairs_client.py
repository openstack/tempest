# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

import json

from tempest.common.rest_client import RestClient


class KeyPairsV3ClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(KeyPairsV3ClientJSON, self).__init__(config, username, password,
                                                   auth_url, tenant_name)
        self.service = self.config.compute.catalog_v3_type

    def list_keypairs(self):
        resp, body = self.get("keypairs")
        body = json.loads(body)
        # Each returned keypair is embedded within an unnecessary 'keypair'
        # element which is a deviation from other resources like floating-ips,
        # servers, etc. A bug?
        # For now we shall adhere to the spec, but the spec for keypairs
        # is yet to be found
        return resp, body['keypairs']

    def get_keypair(self, key_name):
        resp, body = self.get("keypairs/%s" % str(key_name))
        body = json.loads(body)
        return resp, body['keypair']

    def create_keypair(self, name, pub_key=None):
        post_body = {'keypair': {'name': name}}
        if pub_key:
            post_body['keypair']['public_key'] = pub_key
        post_body = json.dumps(post_body)
        resp, body = self.post("keypairs",
                               headers=self.headers, body=post_body)
        body = json.loads(body)
        return resp, body['keypair']

    def delete_keypair(self, key_name):
        return self.delete("keypairs/%s" % str(key_name))
