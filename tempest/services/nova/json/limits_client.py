import json
from tempest.common import rest_client


class LimitsClient(object):

    def __init__(self, username, key, auth_url, tenant_name=None):
        self.client = rest_client.RestClient(config, username, key,
                                             auth_url, tenant_name)

    def get_limits(self):
        resp, body = self.client.get("limits")
        body = json.loads(body)
        return resp, body['limits']

    def get_max_server_meta(self):
        resp, limits_dict = self.get_limits()
        return resp, limits_dict['absolute']['maxServerMeta']

    def get_personality_file_limit(self):
        resp, limits_dict = self.get_limits()
        return resp, limits_dict['absolute']['maxPersonality']

    def get_personality_size_limit(self):
        resp, limits_dict = self.get_limits()
        return resp, limits_dict['absolute']['maxPersonalitySize']
