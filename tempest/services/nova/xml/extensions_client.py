from lxml import etree
from tempest.common.rest_client import RestClientXML
from tempest.services.nova.xml.common import xml_to_json


class ExtensionsClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ExtensionsClientXML, self).__init__(config, username, password,
                                                  auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def _parse_array(self, node):
        array = []
        for child in node:
            array.append(xml_to_json(child))
        return array

    def list_extensions(self):
        url = 'extensions'
        resp, body = self.get(url, self.headers)
        body = self._parse_array(etree.fromstring(body))
        return resp, {'extensions': body}

    def is_enabled(self, extension):
        _, extensions = self.list_extensions()
        exts = extensions['extensions']
        return any([e for e in exts if e['name'] == extension])
