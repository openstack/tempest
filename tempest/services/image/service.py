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

        if self.api_version == 1:
            # We load the client class specific to the API version...
            from glance import client
            creds = {
                'username': config.images.username,
                'password': config.images.password,
                'tenant': config.images.tenant,
                'auth_url': config.images.auth_url,
                'strategy': 'keystone'
            }
            service_token = config.images.service_token
            self._client = client.Client(config.images.host,
                                         config.images.port,
                                         auth_tok=service_token)
        else:
            raise NotImplementedError

    def get_client(self):
        """
        Returns a client object that may be used to query
        the service API.
        """
        assert self._client
        return self._client
