import json
from tempest.common.rest_client import RestClient


class LimitsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(LimitsClientJSON, self).__init__(config, username, password,
                                               auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def get_limits(self):
        resp, body = self.get("limits")
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
