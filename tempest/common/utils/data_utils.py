import random
import urllib


def rand_name(name='test'):
    return name + str(random.randint(1, 99999999999))


def build_url(host, port, apiVer=None, path=None, params=None, https=False):
    """Build the request URL from given host, port, path and parameters"""

    if https:
        url = "https://" + host
    else:
        url = "http://" + host

    if port is not None:
        url += ":" + port
    url += "/"

    if apiVer is not None:
        url += apiVer + "/"

    if path is not None:
        url += path

    if params is not None:
        url += "?"
        url += urllib.urlencode(params)

    return url
