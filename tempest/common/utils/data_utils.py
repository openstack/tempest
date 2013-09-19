# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

import itertools
import random
import re
import urllib

from tempest import exceptions


def rand_name(name='test'):
    return name + str(random.randint(1, 0x7fffffff))


def rand_int_id(start=0, end=0x7fffffff):
    return random.randint(start, end)


def build_url(host, port, api_version=None, path=None,
              params=None, use_ssl=False):
    """Build the request URL from given host, port, path and parameters."""

    pattern = 'v\d\.\d'
    if re.match(pattern, path):
        message = 'Version should not be included in path.'
        raise exceptions.InvalidConfiguration(message=message)

    if use_ssl:
        url = "https://" + host
    else:
        url = "http://" + host

    if port is not None:
        url += ":" + port
    url += "/"

    if api_version is not None:
        url += api_version + "/"

    if path is not None:
        url += path

    if params is not None:
        url += "?"
        url += urllib.urlencode(params)

    return url


def parse_image_id(image_ref):
    """Return the image id from a given image ref."""
    return image_ref.rsplit('/')[-1]


def arbitrary_string(size=4, base_text=None):
    """
    Return size characters from base_text, repeating the base_text infinitely
    if needed.
    """
    if not base_text:
        base_text = 'test'
    return ''.join(itertools.islice(itertools.cycle(base_text), size))
