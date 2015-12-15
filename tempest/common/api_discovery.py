#!/usr/bin/env python

# Copyright 2013 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import httplib2
import json
import logging
import urlparse

LOG = logging.getLogger(__name__)


class ServiceError(Exception):
    pass


class Service(object):
    def __init__(self, name, service_url, token):
        self.name = name
        self.service_url = service_url
        self.headers = {'Accept': 'application/json', 'X-Auth-Token': token}

    def do_get(self, url, top_level=False, top_level_path=""):
        if top_level:
            parts = urlparse.urlparse(url)
            if parts.path != '':
                url = url.replace(parts.path, '/') + top_level_path

        try:
            r, body = httplib2.Http().request(url, 'GET', headers=self.headers)
        except Exception as e:
            LOG.error("Request on service '%s' with url '%s' failed" %
                      (self.name, url))
            raise e
        if r.status >= 400:
            raise ServiceError("Request on service '%s' with url '%s' failed"
                               " with code %d" % (self.name, url, r.status))
        return body

    def get_extensions(self):
        return []

    def get_versions(self):
        return []


class VersionedService(Service):
    def get_versions(self):
        body = self.do_get(self.service_url, top_level=True)
        body = json.loads(body)
        return self.deserialize_versions(body)

    def deserialize_versions(self, body):
        return map(lambda x: x['id'], body['versions'])


class ComputeService(VersionedService):
    def get_extensions(self):
        body = self.do_get(self.service_url + '/extensions')
        body = json.loads(body)
        return map(lambda x: x['alias'], body['extensions'])


class ImageService(VersionedService):
    pass


class NetworkService(VersionedService):
    def get_extensions(self):
        body = self.do_get(self.service_url + '/v2.0/extensions.json')
        body = json.loads(body)
        return map(lambda x: x['alias'], body['extensions'])


class VolumeService(VersionedService):
    def get_extensions(self):
        body = self.do_get(self.service_url + '/extensions')
        body = json.loads(body)
        return map(lambda x: x['alias'], body['extensions'])


class IdentityService(VersionedService):
    def get_extensions(self):
        body = self.do_get(self.service_url + '/extensions')
        body = json.loads(body)
        return map(lambda x: x['alias'], body['extensions']['values'])

    def deserialize_versions(self, body):
        return map(lambda x: x['id'], body['versions']['values'])


class ObjectStorageService(Service):
    def get_extensions(self):
        body = self.do_get(self.service_url, top_level=True,
                           top_level_path="info")
        body = json.loads(body)
        # Remove Swift general information from extensions list
        body.pop('swift')
        return body.keys()


service_dict = {'compute': ComputeService,
                'image': ImageService,
                'network': NetworkService,
                'object-store': ObjectStorageService,
                'volume': VolumeService,
                'identity': IdentityService}


def get_service_class(service_name):
    return service_dict.get(service_name, Service)


def discover(auth_provider, region):
    """
    Returns a dict with discovered apis.
    :param auth_provider: An AuthProvider to obtain service urls.
    :param region: A specific region to use. If the catalog has only one region
    then that region will be used.
    :return: A dict with an entry for the type of each discovered service.
        Each entry has keys for 'extensions' and 'versions'.
    """
    token, auth_data = auth_provider.get_auth()
    services = {}
    for entry in auth_data['serviceCatalog']:
        name = entry['type']
        services[name] = dict()
        for _ep in entry['endpoints']:
            if _ep['region'] == region:
                ep = _ep
                break
        else:
            ep = entry['endpoints'][0]
        services[name]['url'] = ep['publicURL']

        service_class = get_service_class(name)
        service = service_class(name, services[name]['url'], token)
        services[name]['extensions'] = service.get_extensions()
        services[name]['versions'] = service.get_versions()
    return services
