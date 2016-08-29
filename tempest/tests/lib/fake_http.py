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


class fake_httplib2(object):

    def __init__(self, return_type=None, *args, **kwargs):
        self.return_type = return_type

    def request(self, uri, method="GET", body=None, headers=None,
                redirections=5, connection_type=None, chunked=False):
        if not self.return_type:
            fake_headers = fake_http_response(headers)
            return_obj = {
                'uri': uri,
                'method': method,
                'body': body,
                'headers': headers
            }
            return (fake_headers, return_obj)
        elif isinstance(self.return_type, int):
            body = body or "fake_body"
            header_info = {
                'content-type': 'text/plain',
                'content-length': len(body)
            }
            resp_header = fake_http_response(header_info,
                                             status=self.return_type)
            return (resp_header, body)
        else:
            msg = "unsupported return type %s" % self.return_type
            raise TypeError(msg)


class fake_http_response(dict):
    def __init__(self, headers, body=None,
                 version=1.0, status=200, reason="Ok"):
        """Initialization of fake HTTP Response

        :param headers: dict representing HTTP response headers
        :param body: file-like object
        :param version: HTTP Version
        :param status: Response status code
        :param reason: Status code related message.
        """
        self.body = body
        self.status = status
        self['status'] = str(self.status)
        self.reason = reason
        self.version = version
        self.headers = headers

        if headers:
            for key, value in headers.items():
                self[key.lower()] = value

    def getheaders(self):
        return copy.deepcopy(self.headers).items()

    def getheader(self, key, default):
        return self.headers.get(key, default)

    def read(self, amt):
        return self.body.read(amt)
