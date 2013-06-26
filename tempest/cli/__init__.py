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
import os
import shlex
import subprocess

from oslo.config import cfg

import tempest.cli.output_parser
import tempest.test


LOG = logging.getLogger(__name__)

cli_opts = [
    cfg.BoolOpt('enabled',
                default=True,
                help="enable cli tests"),
    cfg.StrOpt('cli_dir',
               default='/usr/local/bin/',
               help="directory where python client binaries are located"),
]

CONF = cfg.CONF
cli_group = cfg.OptGroup(name='cli', title="cli Configuration Options")
CONF.register_group(cli_group)
CONF.register_opts(cli_opts, group=cli_group)


class ClientTestBase(tempest.test.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        if not CONF.cli.enabled:
            msg = "cli testing disabled"
            raise cls.skipException(msg)
        cls.identity = cls.config.identity
        super(ClientTestBase, cls).setUpClass()

    def __init__(self, *args, **kwargs):
        self.parser = tempest.cli.output_parser
        super(ClientTestBase, self).__init__(*args, **kwargs)

    def nova(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes nova command for the given action."""
        return self.cmd_with_auth(
            'nova', action, flags, params, admin, fail_ok)

    def nova_manage(self, action, flags='', params='', fail_ok=False,
                    merge_stderr=False):
        """Executes nova-manage command for the given action."""
        return self.cmd(
            'nova-manage', action, flags, params, fail_ok, merge_stderr)

    def keystone(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes keystone command for the given action."""
        return self.cmd_with_auth(
            'keystone', action, flags, params, admin, fail_ok)

    def glance(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes glance command for the given action."""
        return self.cmd_with_auth(
            'glance', action, flags, params, admin, fail_ok)

    def cmd_with_auth(self, cmd, action, flags='', params='',
                      admin=True, fail_ok=False):
        """Executes given command with auth attributes appended."""
        #TODO(jogo) make admin=False work
        creds = ('--os-username %s --os-tenant-name %s --os-password %s '
                 '--os-auth-url %s ' % (self.identity.admin_username,
                 self.identity.admin_tenant_name, self.identity.admin_password,
                 self.identity.uri))
        flags = creds + ' ' + flags
        return self.cmd(cmd, action, flags, params, fail_ok)

    def check_output(self, cmd, **kwargs):
        # substitutes subprocess.check_output which is not in python2.6
        kwargs['stdout'] = subprocess.PIPE
        proc = subprocess.Popen(cmd, **kwargs)
        output = proc.communicate()[0]
        if proc.returncode != 0:
            raise CommandFailed(proc.returncode, cmd, output)
        return output

    def cmd(self, cmd, action, flags='', params='', fail_ok=False,
            merge_stderr=False):
        """Executes specified command for the given action."""
        cmd = ' '.join([os.path.join(CONF.cli.cli_dir, cmd),
                        flags, action, params])
        LOG.info("running: '%s'" % cmd)
        cmd = shlex.split(cmd)
        try:
            if merge_stderr:
                result = self.check_output(cmd, stderr=subprocess.STDOUT)
            else:
                with open('/dev/null', 'w') as devnull:
                    result = self.check_output(cmd, stderr=devnull)
        except subprocess.CalledProcessError as e:
            LOG.error("command output:\n%s" % e.output)
            raise
        return result

    def assertTableStruct(self, items, field_names):
        """Verify that all items has keys listed in field_names."""
        for item in items:
            for field in field_names:
                self.assertIn(field, item)


class CommandFailed(subprocess.CalledProcessError):
    # adds output attribute for python2.6
    def __init__(self, returncode, cmd, output):
        super(CommandFailed, self).__init__(returncode, cmd)
        self.output = output
