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
import string
import uuid

from oslo_utils import uuidutils
import six.moves


def rand_uuid():
    """Generate a random UUID string

    :return: a random UUID (e.g. '1dc12c7d-60eb-4b61-a7a2-17cf210155b6')
    :rtype: string
    """
    return uuidutils.generate_uuid()


def rand_uuid_hex():
    """Generate a random UUID hex string

    :return: a random UUID (e.g. '0b98cf96d90447bda4b46f31aeb1508c')
    :rtype: string
    """
    return uuid.uuid4().hex


def rand_name(name='', prefix='tempest'):
    """Generate a random name that includes a random number

    :param str name: The name that you want to include
    :param str prefix: The prefix that you want to include
    :return: a random name. The format is
             '<prefix>-<name>-<random number>'.
             (e.g. 'prefixfoo-namebar-154876201')
    :rtype: string
    """
    rand_name = str(random.randint(1, 0x7fffffff))
    if name:
        rand_name = name + '-' + rand_name
    if prefix:
        rand_name = prefix + '-' + rand_name
    return rand_name


def rand_password(length=15):
    """Generate a random password

    :param int length: The length of password that you expect to set
                       (If it's smaller than 3, it's same as 3.)
    :return: a random password. The format is
        ``'<random upper letter>-<random number>-<random special character>
        -<random ascii letters or digit characters or special symbols>'``
        (e.g. ``G2*ac8&lKFFgh%2``)
    :rtype: string
    """
    upper = random.choice(string.ascii_uppercase)
    ascii_char = string.ascii_letters
    digits = string.digits
    digit = random.choice(string.digits)
    puncs = '~!@#%^&*_=+'
    punc = random.choice(puncs)
    seed = ascii_char + digits + puncs
    pre = upper + digit + punc
    password = pre + ''.join(random.choice(seed) for x in range(length - 3))
    return password


def rand_url():
    """Generate a random url that includes a random number

    :return: a random url. The format is 'https://url-<random number>.com'.
             (e.g. 'https://url-154876201.com')
    :rtype: string
    """
    randbits = str(random.randint(1, 0x7fffffff))
    return 'https://url-' + randbits + '.com'


def rand_int_id(start=0, end=0x7fffffff):
    """Generate a random integer value

    :param int start: The value that you expect to start here
    :param int end: The value that you expect to end here
    :return: a random integer value
    :rtype: int
    """
    return random.randint(start, end)


def rand_mac_address():
    """Generate an Ethernet MAC address

    :return: an random Ethernet MAC address
    :rtype: string
    """
    # NOTE(vish): We would prefer to use 0xfe here to ensure that linux
    #             bridge mac addresses don't change, but it appears to
    #             conflict with libvirt, so we use the next highest octet
    #             that has the unicast and locally administered bits set
    #             properly: 0xfa.
    #             Discussion: https://bugs.launchpad.net/nova/+bug/921838
    mac = [0xfa, 0x16, 0x3e,
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(["%02x" % x for x in mac])


def rand_infiniband_guid_address():
    """Generate an Infiniband GUID address

    :return: an random Infiniband GUID address
    :rtype: string
    """
    guid = []
    for i in range(8):
        guid.append("%02x" % random.randint(0x00, 0xff))
    return ':'.join(guid)


def parse_image_id(image_ref):
    """Return the image id from a given image ref

    This function just returns the last word of the given image ref string
    splitting with '/'.
    :param str image_ref: a string that includes the image id
    :return: the image id string
    :rtype: string
    """
    return image_ref.rsplit('/')[-1]


def arbitrary_string(size=4, base_text=None):
    """Return size characters from base_text

    This generates a string with an arbitrary number of characters, generated
    by looping the base_text string. If the size is smaller than the size of
    base_text, returning string is shrunk to the size.
    :param int size: a returning characters size
    :param str base_text: a string you want to repeat
    :return: size string
    :rtype: string
    """
    if not base_text:
        base_text = 'test'
    return ''.join(itertools.islice(itertools.cycle(base_text), size))


def random_bytes(size=1024):
    """Return size randomly selected bytes as a string

    :param int size: a returning bytes size
    :return: size randomly bytes
    :rtype: string
    """
    return b''.join([six.int2byte(random.randint(0, 255))
                     for i in range(size)])


# Courtesy of http://stackoverflow.com/a/312464
def chunkify(sequence, chunksize):
    """Yield successive chunks from `sequence`."""
    for i in range(0, len(sequence), chunksize):
        yield sequence[i:i + chunksize]
