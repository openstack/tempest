# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

"""
Image Service class, which acts as a descriptor for the OpenStack Images
service running in the test environment.
"""

from tempest.services import Service as BaseService


class Service(BaseService):

    def __init__(self, config):
        """
        Initializes the service.

        :param config: `tempest.config.Config` object
        """
        self.config = config

        # Determine the Images API version
        self.api_version = int(config.images.api_version)

        # We load the client class specific to the API version...
        if self.api_version == 1:
            import glanceclient
            import keystoneclient.v2_0.client

            dscv = self.config.identity.disable_ssl_certificate_validation
            auth_url = self.config.identity.uri
            keystone = keystoneclient.v2_0.client.Client(
                    username=config.compute.username,
                    password=config.compute.password,
                    tenant_name=config.compute.tenant_name,
                    auth_url=auth_url,
                    insecure=dscv)
            token = keystone.auth_token
            endpoint = keystone.service_catalog.url_for(
                    service_type='image',
                    endpoint_type='publicURL')

            self._client = glanceclient.Client('1',
                                               endpoint=endpoint,
                                               token=token,
                                               insecure=dscv)
        else:
            raise NotImplementedError

    def get_client(self):
        """
        Returns a client object that may be used to query
        the service API.
        """
        assert self._client
        return self._client
