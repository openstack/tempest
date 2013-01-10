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

from tempest.services.compute.json.quotas_client import QuotasClientJSON


class AdminQuotasClientJSON(QuotasClientJSON):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(AdminQuotasClientJSON, self).__init__(config, username, password,
                                                    auth_url, tenant_name)

    def update_quota_set(self, tenant_id, injected_file_content_bytes=None,
                         metadata_items=None, ram=None, floating_ips=None,
                         key_pairs=None, instances=None,
                         security_group_rules=None, injected_files=None,
                         cores=None, injected_file_path_bytes=None,
                         security_groups=None):
        """
        Updates the tenant's quota limits for one or more resources
        """
        post_body = {}

        if injected_file_content_bytes >= 0:
            post_body['injected_file_content_bytes'] = \
                injected_file_content_bytes

        if metadata_items >= 0:
            post_body['metadata_items'] = metadata_items

        if ram >= 0:
            post_body['ram'] = ram

        if floating_ips >= 0:
            post_body['floating_ips'] = floating_ips

        if key_pairs >= 0:
            post_body['key_pairs'] = key_pairs

        if instances >= 0:
            post_body['instances'] = instances

        if security_group_rules >= 0:
            post_body['security_group_rules'] = security_group_rules

        if injected_files >= 0:
            post_body['injected_files'] = injected_files

        if cores >= 0:
            post_body['cores'] = cores

        if injected_file_path_bytes >= 0:
            post_body['injected_file_path_bytes'] = injected_file_path_bytes

        if security_groups >= 0:
            post_body['security_groups'] = security_groups

        post_body = json.dumps({'quota_set': post_body})
        resp, body = self.put('os-quota-sets/%s' % str(tenant_id), post_body,
                              self.headers)

        body = json.loads(body)
        return resp, body['quota_set']
