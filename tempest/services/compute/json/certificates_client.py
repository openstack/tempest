# Copyright 2013 IBM Corp
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
from tempest import config

CONF = config.CONF


class CertificatesClientJSON(RestClient):

    def __init__(self, auth_provider):
        super(CertificatesClientJSON, self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def get_certificate(self, id):
        url = "os-certificates/%s" % (id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['certificate']

    def create_certificate(self):
        """create certificates."""
        url = "os-certificates"
        resp, body = self.post(url, None, self.headers)
        body = json.loads(body)
        return resp, body['certificate']
