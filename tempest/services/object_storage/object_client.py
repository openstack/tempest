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

import re
from tempest.common.rest_client import RestClient


class ObjectClient(RestClient):
    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ObjectClient, self).__init__(config, username, password,
                                           auth_url, tenant_name)

        self.service = self.config.object_storage.catalog_type

    def create_object(self, container, object_name, data):
        """Create storage object"""

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.put(url, data, self.headers)
        return resp, body

    def update_object(self, container, object_name, data):
        """Upload data to replace current storage object"""
        return create_object(container, object_name, data)

    def delete_object(self, container, object_name):
        """Delete storage object"""
        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.delete(url)
        return resp, body

    def update_object_metadata(self, container, object_name, metadata,
                               metadata_prefix='X-Object-Meta-'):
        """Add, remove, or change X-Object-Meta metadata for storage object"""

        headers = {}
        for key in metadata:
            headers["%s%s" % (str(metadata_prefix), str(key))] = metadata[key]

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.post(url, None, headers=headers)
        return resp, body

    def list_object_metadata(self, container, object_name):
        """List all storage object X-Object-Meta- metadata"""

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.head(url)
        return resp, body
