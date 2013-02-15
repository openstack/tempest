# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging
import shlex
import subprocess

import testtools

import cli

from tempest import config
from tempest.openstack.common import cfg


CONF = cfg.CONF


LOG = logging.getLogger(__name__)


class SimpleReadOnlyNovaCLientTest(testtools.TestCase):

    """
    This is a first pass at a simple read only python-novaclient test. This
    only exercises client commands that are read only.

    This should test commands:
    * as a regular user
    * as a admin user
    * with and without optional parameters
    * initially just check return codes, and later test command outputs

    """

    @classmethod
    def setUpClass(cls):
        if not CONF.cli.enabled:
            msg = "cli testing disabled"
            raise cls.skipException(msg)
        cls.identity = config.TempestConfig().identity
        super(SimpleReadOnlyNovaCLientTest, cls).setUpClass()

    def nova(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes nova command for the given action."""
        #TODO(jogo) make admin=False work
        creds = ('--os-username %s --os-tenant-name %s --os-password %s '
                 '--os-auth-url %s ' % (self.identity.admin_username,
                 self.identity.admin_tenant_name, self.identity.admin_password,
                 self.identity.uri))
        flags = creds + ' ' + flags
        cmd = ' '.join([CONF.cli.cli_dir + 'nova', flags, action, params])
        LOG.info("running: '%s'" % cmd)
        cmd = shlex.split(cmd)
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return result

    def test_admin_version(self):
        self.nova('', flags='--version')

    def test_admin_timing(self):
        self.nova('list', flags='--timing')

    def test_admin_timeout(self):
        self.nova('list', flags='--timeout 2')

    def test_admin_debug_list(self):
        self.nova('list', flags='--debug')

    def test_admin_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.nova,
                          'this-does-nova-exist')

    def test_admin_aggregate_list(self):
        self.nova('aggregate-list')

    def test_admin_cloudpipe_list(self):
        self.nova('cloudpipe-list')

    def test_admin_image_list(self):
        self.nova('image-list')

    def test_admin_dns_domains(self):
        self.nova('dns-domains')

    def test_admin_flavor_list(self):
        self.nova('flavor-list')

    #TODO(jogo) add more tests
