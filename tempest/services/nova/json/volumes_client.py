from tempest.common import rest_client
import json


class VolumesClient(object):

    def __init__(self, config, username, key, auth_url, tenant_name=None):
        self.config = config
        catalog_type = self.config.compute.catalog_type
        self.client = rest_client.RestClient(config, username, key, auth_url,
                                             catalog_type, tenant_name)

    def list_volumes(self, params=None):
        """List all the volumes created"""
        url = 'os-volumes'
        if params != None:
            param_list = []
            for param, value in params.iteritems():
                param_list.append("%s=%s&" % (param, value))

            url += '?' + ' '.join(param_list)

        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body['volumes']

    def get_volume(self, volume_id):
        """Returns the details of a single volume"""
        url = "os-volumes/%s" % str(volume_id)
        resp, body = self.client.get(url)
        body = json.loads(body)
        return resp, body['volume']

    def delete_volume(self, volume_id):
        """Deletes the Specified Volume"""
        return self.client.delete("os-volumes/%s" % str(volume_id))
