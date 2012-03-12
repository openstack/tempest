import random
import re
import urllib
from tempest import exceptions


def rand_name(name='test'):
    return name + str(random.randint(1, 99999999999))


def build_url(host, port, api_version=None, path=None,
              params=None, use_ssl=False):
    """Build the request URL from given host, port, path and parameters"""

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
