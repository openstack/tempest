# Copyright 2013 IBM Corp.
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

import copy

import httplib2


class fake_httplib2(object):

    def __init__(self, return_type=None, *args, **kwargs):
        self.return_type = return_type

    def request(self, uri, method="GET", body=None, headers=None,
                redirections=5, connection_type=None):
        if not self.return_type:
            fake_headers = httplib2.Response(headers)
            return_obj = {
                'uri': uri,
                'method': method,
                'body': body,
                'headers': headers
            }
            return (fake_headers, return_obj)
        elif isinstance(self.return_type, int):
            body = "fake_body"
            header_info = {
                'content-type': 'text/plain',
                'status': str(self.return_type),
                'content-length': len(body)
            }
            resp_header = httplib2.Response(header_info)
            return (resp_header, body)
        else:
            msg = "unsupported return type %s" % self.return_type
            raise TypeError(msg)


class fake_httplib(object):
    def __init__(self, headers, body=None,
                 version=1.0, status=200, reason="Ok"):
        """
        :param headers: dict representing HTTP response headers
        :param body: file-like object
        :param version: HTTP Version
        :param status: Response status code
        :param reason: Status code related message.
        """
        self.body = body
        self.status = status
        self.reason = reason
        self.version = version
        self.headers = headers

    def getheaders(self):
        return copy.deepcopy(self.headers).items()

    def getheader(self, key, default):
        return self.headers.get(key, default)

    def read(self, amt):
        return self.body.read(amt)
