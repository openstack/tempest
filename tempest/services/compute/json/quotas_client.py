# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 NTT Data
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


class QuotasClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(QuotasClientJSON, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def get_quota_set(self, tenant_id):
        """List the quota set for a tenant."""

        url = 'os-quota-sets/%s' % str(tenant_id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['quota_set']

    def get_default_quota_set(self, tenant_id):
        """List the default quota set for a tenant."""

        url = 'os-quota-sets/%s/defaults' % str(tenant_id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['quota_set']

    def update_quota_set(self, tenant_id, injected_file_content_bytes=None,
                         metadata_items=None, ram=None, floating_ips=None,
                         fixed_ips=None, key_pairs=None, instances=None,
                         security_group_rules=None, injected_files=None,
                         cores=None, injected_file_path_bytes=None,
                         security_groups=None):
        """
        Updates the tenant's quota limits for one or more resources
        """
        post_body = {}

        if injected_file_content_bytes is not None:
            post_body['injected_file_content_bytes'] = \
                injected_file_content_bytes

        if metadata_items is not None:
            post_body['metadata_items'] = metadata_items

        if ram is not None:
            post_body['ram'] = ram

        if floating_ips is not None:
            post_body['floating_ips'] = floating_ips

        if fixed_ips is not None:
            post_body['fixed_ips'] = fixed_ips

        if key_pairs is not None:
            post_body['key_pairs'] = key_pairs

        if instances is not None:
            post_body['instances'] = instances

        if security_group_rules is not None:
            post_body['security_group_rules'] = security_group_rules

        if injected_files is not None:
            post_body['injected_files'] = injected_files

        if cores is not None:
            post_body['cores'] = cores

        if injected_file_path_bytes is not None:
            post_body['injected_file_path_bytes'] = injected_file_path_bytes

        if security_groups is not None:
            post_body['security_groups'] = security_groups

        post_body = json.dumps({'quota_set': post_body})
        resp, body = self.put('os-quota-sets/%s' % str(tenant_id), post_body,
                              self.headers)

        body = json.loads(body)
        return resp, body['quota_set']
