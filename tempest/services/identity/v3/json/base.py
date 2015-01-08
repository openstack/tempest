# Copyright 2014 NEC Corporation.  All rights reserved.
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

from tempest.common import service_client
from tempest import config

CONF = config.CONF


class IdentityV3Client(service_client.ServiceClient):
    """
    Base identity v3 client class
    """

    def __init__(self, auth_provider):
        super(IdentityV3Client, self).__init__(
            auth_provider,
            CONF.identity.catalog_type,
            CONF.identity.region,
            endpoint_type='adminURL')
        self.api_version = "v3"
