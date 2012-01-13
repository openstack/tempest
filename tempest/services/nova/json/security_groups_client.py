from tempest.common import rest_client
import json


class SecurityGroupsClient(object):

    def __init__(self, config, username, key, auth_url, tenant_name=None):
        self.config = config
        self.client = rest_client.RestClient(config, username, key,
                                             auth_url, 'nova', tenant_name)

    def list_security_groups(self, params=None):
        """List all security groups for a user"""

        url = 'os-security-groups'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url += '?' + ' '.join(param_list)

        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body

    def list_security_groups_with_detail(self, params=None):
        """List security groups with detail"""

        url = 'os-security-groups/detail'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url += '?' + ' '.join(param_list)

        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body
