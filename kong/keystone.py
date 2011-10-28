import json

import kong.common.http
from kong import exceptions


class API(kong.common.http.Client):
    """Barebones Keystone HTTP API client."""

    def __init__(self, service_host, service_port):
        super(API, self).__init__(service_host, service_port, 'v2.0')

        #TODO(bcwaldon): This is a hack, we should clean up the superclass
        self.management_url = self.base_url

    def get_token(self, user, password, tenant_id):
        headers = {'content-type': 'application/json'}

        body = {
            "auth": {
                "passwordCredentials":{
                    "username": user,
                    "password": password,
                },
                "tenantId": tenant_id,
            },
        }

        response, content = self.request('POST', '/tokens',
                                         headers=headers,
                                         body=json.dumps(body))

        res_body = json.loads(content)
        return res_body['access']['token']['id']
