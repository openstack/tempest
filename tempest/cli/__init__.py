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
from tempest_lib.cli import output_parser
import testtools

from tempest.common import credentials
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


class ClientTestBase(test.BaseTestCase):

    @classmethod
    def skip_checks(cls):
        super(ClientTestBase, cls).skip_checks()
        if not CONF.identity_feature_enabled.api_v2:
            raise cls.skipException("CLI clients rely on identity v2 API, "
                                    "which is configured as not available")

    @classmethod
    def resource_setup(cls):
        if not CONF.cli.enabled:
            msg = "cli testing disabled"
            raise cls.skipException(msg)
        super(ClientTestBase, cls).resource_setup()
        cls.isolated_creds = credentials.get_isolated_credentials(cls.__name__)
        cls.creds = cls.isolated_creds.get_admin_creds()

    def _get_clients(self):
        clients = base.CLIClient(self.creds.username,
                                 self.creds.password,
                                 self.creds.tenant_name,
                                 CONF.identity.uri, CONF.cli.cli_dir)
        return clients

    # TODO(mtreinish): The following code is basically copied from tempest-lib.
    # The base cli test class in tempest-lib 0.0.1 doesn't work as a mixin like
    # is needed here. The code below should be removed when tempest-lib
    # provides a way to provide this functionality
    def setUp(self):
        super(ClientTestBase, self).setUp()
        self.clients = self._get_clients()
        self.parser = output_parser

    def assertTableStruct(self, items, field_names):
        """Verify that all items has keys listed in field_names.

        :param items: items to assert are field names in the output table
        :type items: list
        :param field_names: field names from the output table of the cmd
        :type field_names: list
        """
        for item in items:
            for field in field_names:
                self.assertIn(field, item)

    def assertFirstLineStartsWith(self, lines, beginning):
        """Verify that the first line starts with a string

        :param lines: strings for each line of output
        :type lines: list
        :param beginning: verify this is at the beginning of the first line
        :type beginning: string
        """
        self.assertTrue(lines[0].startswith(beginning),
                        msg=('Beginning of first line has invalid content: %s'
                             % lines[:3]))
