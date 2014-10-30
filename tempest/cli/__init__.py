# Copyright 2013 OpenStack Foundation
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

import functools

from tempest_lib.cli import base
import testtools

from tempest import config
from tempest import exceptions
from tempest.openstack.common import versionutils
from tempest import test


CONF = config.CONF


def check_client_version(client, version):
    """Checks if the client's version is compatible with the given version

    @param client: The client to check.
    @param version: The version to compare against.
    @return: True if the client version is compatible with the given version
             parameter, False otherwise.
    """
    current_version = base.execute(client, '', params='--version',
                                   merge_stderr=True, cli_dir=CONF.cli.cli_dir)

    if not current_version.strip():
        raise exceptions.TempestException('"%s --version" output was empty' %
                                          client)

    return versionutils.is_compatible(version, current_version,
                                      same_major=False)


def min_client_version(*args, **kwargs):
    """A decorator to skip tests if the client used isn't of the right version.

    @param client: The client command to run. For python-novaclient, this is
                   'nova', for python-cinderclient this is 'cinder', etc.
    @param version: The minimum version required to run the CLI test.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*func_args, **func_kwargs):
            if not check_client_version(kwargs['client'], kwargs['version']):
                msg = "requires %s client version >= %s" % (kwargs['client'],
                                                            kwargs['version'])
                raise testtools.TestCase.skipException(msg)
            return func(*func_args, **func_kwargs)
        return wrapper
    return decorator


class ClientTestBase(base.ClientTestBase, test.BaseTestCase):
    @classmethod
    def resource_setup(cls):
        if not CONF.cli.enabled:
            msg = "cli testing disabled"
            raise cls.skipException(msg)
        super(ClientTestBase, cls).resource_setup()

    def _get_clients(self):
        clients = base.CLIClient(CONF.identity.admin_username,
                                 CONF.identity.admin_password,
                                 CONF.identity.admin_tenant_name,
                                 CONF.identity.uri, CONF.cli.cli_dir)
        return clients
