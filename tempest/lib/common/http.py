# Copyright 2016 OpenStack Foundation
# All Rights Reserved.
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

import urllib3


class ClosingProxyHttp(urllib3.ProxyManager):
    def __init__(self, proxy_url, disable_ssl_certificate_validation=False,
                 ca_certs=None, timeout=None, follow_redirects=True):
        self.follow_redirects = follow_redirects
        kwargs = {}

        if disable_ssl_certificate_validation:
            urllib3.disable_warnings()
            kwargs['cert_reqs'] = 'CERT_NONE'
        elif ca_certs:
            kwargs['cert_reqs'] = 'CERT_REQUIRED'
            kwargs['ca_certs'] = ca_certs

        if timeout:
            kwargs['timeout'] = timeout

        super(ClosingProxyHttp, self).__init__(proxy_url, **kwargs)

    def request(self, url, method, *args, **kwargs):

        class Response(dict):
            def __init__(self, info):
                for key, value in info.getheaders().items():
                    self[key.lower()] = value
                self.status = info.status
                self['status'] = str(self.status)
                self.reason = info.reason
                self.version = info.version
                self['content-location'] = url

        original_headers = kwargs.get('headers', {})
        new_headers = dict(original_headers, connection='close')
        new_kwargs = dict(kwargs, headers=new_headers)

        if self.follow_redirects:
            # Follow up to 5 redirections. Don't raise an exception if
            # it's exceeded but return the HTTP 3XX response instead.
            retry = urllib3.util.Retry(raise_on_redirect=False, redirect=5)
        else:
            # Do not follow redirections. Don't raise an exception if
            # a redirect is found, but return the HTTP 3XX response instead.
            retry = urllib3.util.Retry(redirect=False)
        r = super(ClosingProxyHttp, self).request(method, url, retries=retry,
                                                  *args, **new_kwargs)
        return Response(r), r.data


class ClosingHttp(urllib3.poolmanager.PoolManager):
    def __init__(self, disable_ssl_certificate_validation=False,
                 ca_certs=None, timeout=None, follow_redirects=True):
        self.follow_redirects = follow_redirects
        kwargs = {}

        if disable_ssl_certificate_validation:
            urllib3.disable_warnings()
            kwargs['cert_reqs'] = 'CERT_NONE'
        elif ca_certs:
            kwargs['cert_reqs'] = 'CERT_REQUIRED'
            kwargs['ca_certs'] = ca_certs

        if timeout:
            kwargs['timeout'] = timeout

        super(ClosingHttp, self).__init__(**kwargs)

    def request(self, url, method, *args, **kwargs):

        class Response(dict):
            def __init__(self, info):
                for key, value in info.getheaders().items():
                    # We assume HTTP header name to be string, not random
                    # bytes, thus ensure we have string keys.
                    self[str(key).lower()] = value
                self.status = info.status
                self['status'] = str(self.status)
                self.reason = info.reason
                self.version = info.version
                self['content-location'] = url

        original_headers = kwargs.get('headers', {})
        new_headers = dict(original_headers, connection='close')
        new_kwargs = dict(kwargs, headers=new_headers)

        if self.follow_redirects:
            # Follow up to 5 redirections. Don't raise an exception if
            # it's exceeded but return the HTTP 3XX response instead.
            retry = urllib3.util.Retry(raise_on_redirect=False, redirect=5)
        else:
            # Do not follow redirections. Don't raise an exception if
            # a redirect is found, but return the HTTP 3XX response instead.
            retry = urllib3.util.Retry(redirect=False)
        r = super(ClosingHttp, self).request(method, url, retries=retry,
                                             *args, **new_kwargs)
        return Response(r), r.data
