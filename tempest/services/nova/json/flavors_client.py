from tempest.common.rest_client import RestClient
import json


class FlavorsClient(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(FlavorsClient, self).__init__(config, username, password,
                                            auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def list_flavors(self, params=None):
        url = 'flavors'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url = "flavors?" + "".join(param_list)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['flavors']

    def list_flavors_with_detail(self, params=None):
        url = 'flavors/detail'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url = "flavors/detail?" + "".join(param_list)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['flavors']

    def get_flavor_details(self, flavor_id):
        resp, body = self.get("flavors/%s" % str(flavor_id))
        body = json.loads(body)
        return resp, body['flavor']

    def create_flavor(self, name, ram, vcpus, disk, ephemeral, flavor_id,
                    swap, rxtx):
        """Creates a new flavor or instance type"""
        post_body = {
                'name': name,
                'ram': ram,
                'vcpus': vcpus,
                'disk': disk,
                'OS-FLV-EXT-DATA:ephemeral': ephemeral,
                'id': flavor_id,
                'swap': swap,
                'rxtx_factor': rxtx
            }

        post_body = json.dumps({'flavor': post_body})
        resp, body = self.post('flavors', post_body, self.headers)

        body = json.loads(body)
        return resp, body['flavor']

    def delete_flavor(self, flavor_id):
        """Deletes the given flavor"""
        return self.delete("flavors/%s" % str(flavor_id))
