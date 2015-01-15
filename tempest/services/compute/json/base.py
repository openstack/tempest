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


class ComputeClient(service_client.ServiceClient):
    """
    Base compute client class
    """

    def __init__(self, auth_provider,
                 build_interval=None, build_timeout=None):
        if build_interval is None:
            build_interval = CONF.compute.build_interval
        if build_timeout is None:
            build_timeout = CONF.compute.build_timeout

        super(ComputeClient, self).__init__(
            auth_provider,
            CONF.compute.catalog_type,
            CONF.compute.region or CONF.identity.region,
            endpoint_type=CONF.compute.endpoint_type,
            build_interval=build_interval,
            build_timeout=build_timeout)
