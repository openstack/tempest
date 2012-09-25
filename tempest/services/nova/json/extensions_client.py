from tempest.common.rest_client import RestClient
import json


class ExtensionsClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ExtensionsClientJSON, self).__init__(config, username, password,
                                                   auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def list_extensions(self):
        url = 'extensions'
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def is_enabled(self, extension):
        _, extensions = self.list_extensions()
        exts = extensions['extensions']
        return any([e for e in exts if e['name'] == extension])
