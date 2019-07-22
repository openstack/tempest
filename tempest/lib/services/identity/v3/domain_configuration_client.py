# Copyright 2017 AT&T Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class DomainConfigurationClient(rest_client.RestClient):
    api_version = "v3"

    def show_default_config_settings(self):
        """Show default configuration settings.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-default-configuration-settings
        """
        url = 'domains/config/default'
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_default_group_config(self, group):
        """Show default configuration for a group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-default-configuration-for-a-group
        """
        url = 'domains/config/%s/default' % group
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_default_group_option(self, group, option):
        """Show default option for a group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-default-option-for-a-group
        """
        url = 'domains/config/%s/%s/default' % (group, option)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_domain_group_option_config(self, domain_id, group, option):
        """Show domain group option configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-domain-group-option-configuration
        """
        url = 'domains/%s/config/%s/%s' % (domain_id, group, option)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_domain_group_option_config(self, domain_id, group, option,
                                          **kwargs):
        """Update domain group option configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-domain-group-option-configuration
        """
        url = 'domains/%s/config/%s/%s' % (domain_id, group, option)
        resp, body = self.patch(url, json.dumps({'config': kwargs}))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_domain_group_option_config(self, domain_id, group, option):
        """Delete domain group option configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#delete-domain-group-option-configuration
        """
        url = 'domains/%s/config/%s/%s' % (domain_id, group, option)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_domain_group_config(self, domain_id, group):
        """Shows details for a domain group configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-domain-group-configuration
        """
        url = 'domains/%s/config/%s' % (domain_id, group)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_domain_group_config(self, domain_id, group, **kwargs):
        """Update domain group configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-domain-group-configuration
        """
        url = 'domains/%s/config/%s' % (domain_id, group)
        resp, body = self.patch(url, json.dumps({'config': kwargs}))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_domain_group_config(self, domain_id, group):
        """Delete domain group configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#delete-domain-group-configuration
        """
        url = 'domains/%s/config/%s' % (domain_id, group)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_domain_config(self, domain_id, **kwargs):
        """Create domain configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#create-domain-configuration
        """
        url = 'domains/%s/config' % domain_id
        resp, body = self.put(url, json.dumps({'config': kwargs}))
        self.expected_success([200, 201], resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_domain_config(self, domain_id):
        """Show domain configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#show-domain-configuration
        """
        url = 'domains/%s/config' % domain_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_domain_config(self, domain_id, **kwargs):
        """Update domain configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-domain-configuration
        """
        url = 'domains/%s/config' % domain_id
        resp, body = self.patch(url, json.dumps({'config': kwargs}))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_domain_config(self, domain_id):
        """Delete domain configuration.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#delete-domain-configuration
        """
        url = 'domains/%s/config' % domain_id
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
