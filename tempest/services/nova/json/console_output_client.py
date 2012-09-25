from tempest.common.rest_client import RestClient
import json


class ConsoleOutputsClient(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ConsoleOutputsClient, self).__init__(config, username, password,
                                                   auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def get_console_output(self, server_id, length):
        post_body = {'os-getConsoleOutput': {'length': length}}
        url = "/servers/%s/action" % server_id
        post_body = json.dumps(post_body)
        resp, body = self.post(url, post_body, self.headers)
        body = json.loads(body)
        return resp, body['output']
