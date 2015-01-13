# Copyright 2015 NEC Corporation.  All rights reserved.
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

from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class ServiceClient(rest_client.RestClient):

    def __init__(self, auth_provider, service, region,
                 endpoint_type=None, build_interval=None, build_timeout=None):
        params = {
            'disable_ssl_certificate_validation':
                CONF.identity.disable_ssl_certificate_validation,
            'ca_certs': CONF.identity.ca_certificates_file,
            'trace_requests': CONF.debug.trace_requests
        }
        if endpoint_type is not None:
            params.update({'endpoint_type': endpoint_type})
        if build_interval is not None:
            params.update({'build_interval': build_interval})
        if build_timeout is not None:
            params.update({'build_timeout': build_timeout})
        super(ServiceClient, self).__init__(auth_provider, service, region,
                                            **params)
