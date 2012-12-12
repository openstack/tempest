import json

from tempest.common.rest_client import RestClient


class HostsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(HostsClientJSON, self).__init__(config, username, password,
                                              auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def list_hosts(self):
        """Lists all hosts"""

        url = 'os-hosts'
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['hosts']
