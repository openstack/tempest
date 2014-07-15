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

import os
import shlex
import subprocess

import tempest.cli.output_parser
from tempest import config
from tempest.openstack.common import log as logging
import tempest.test


LOG = logging.getLogger(__name__)

CONF = config.CONF


class ClientTestBase(tempest.test.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        if not CONF.cli.enabled:
            msg = "cli testing disabled"
            raise cls.skipException(msg)
        super(ClientTestBase, cls).setUpClass()

    def __init__(self, *args, **kwargs):
        self.parser = tempest.cli.output_parser
        super(ClientTestBase, self).__init__(*args, **kwargs)

    def nova(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes nova command for the given action."""
        flags += ' --endpoint-type %s' % CONF.compute.endpoint_type
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
        flags += ' --os-endpoint-type %s' % CONF.image.endpoint_type
        return self.cmd_with_auth(
            'glance', action, flags, params, admin, fail_ok)

    def ceilometer(self, action, flags='', params='', admin=True,
                   fail_ok=False):
        """Executes ceilometer command for the given action."""
        flags += ' --os-endpoint-type %s' % CONF.telemetry.endpoint_type
        return self.cmd_with_auth(
            'ceilometer', action, flags, params, admin, fail_ok)

    def heat(self, action, flags='', params='', admin=True,
             fail_ok=False):
        """Executes heat command for the given action."""
        flags += ' --os-endpoint-type %s' % CONF.orchestration.endpoint_type
        return self.cmd_with_auth(
            'heat', action, flags, params, admin, fail_ok)

    def cinder(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes cinder command for the given action."""
        flags += ' --endpoint-type %s' % CONF.volume.endpoint_type
        return self.cmd_with_auth(
            'cinder', action, flags, params, admin, fail_ok)

    def swift(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes swift command for the given action."""
        flags += ' --os-endpoint-type %s' % CONF.object_storage.endpoint_type
        return self.cmd_with_auth(
            'swift', action, flags, params, admin, fail_ok)

    def neutron(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes neutron command for the given action."""
        flags += ' --endpoint-type %s' % CONF.network.endpoint_type
        return self.cmd_with_auth(
            'neutron', action, flags, params, admin, fail_ok)

    def sahara(self, action, flags='', params='', admin=True,
               fail_ok=False, merge_stderr=True):
        """Executes sahara command for the given action."""
        flags += ' --endpoint-type %s' % CONF.data_processing.endpoint_type
        return self.cmd_with_auth(
            'sahara', action, flags, params, admin, fail_ok, merge_stderr)

    def cmd_with_auth(self, cmd, action, flags='', params='',
                      admin=True, fail_ok=False, merge_stderr=False):
        """Executes given command with auth attributes appended."""
        # TODO(jogo) make admin=False work
        creds = ('--os-username %s --os-tenant-name %s --os-password %s '
                 '--os-auth-url %s' %
                 (CONF.identity.admin_username,
                  CONF.identity.admin_tenant_name,
                  CONF.identity.admin_password,
                  CONF.identity.uri))
        flags = creds + ' ' + flags
        return self.cmd(cmd, action, flags, params, fail_ok, merge_stderr)

    def cmd(self, cmd, action, flags='', params='', fail_ok=False,
            merge_stderr=False):
        """Executes specified command for the given action."""
        cmd = ' '.join([os.path.join(CONF.cli.cli_dir, cmd),
                        flags, action, params])
        LOG.info("running: '%s'" % cmd)
        cmd = shlex.split(cmd)
        result = ''
        result_err = ''
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT if merge_stderr else subprocess.PIPE
        proc = subprocess.Popen(
            cmd, stdout=stdout, stderr=stderr)
        result, result_err = proc.communicate()
        if not fail_ok and proc.returncode != 0:
            raise CommandFailed(proc.returncode,
                                cmd,
                                result,
                                stderr=result_err)
        return result

    def assertTableStruct(self, items, field_names):
        """Verify that all items has keys listed in field_names."""
        for item in items:
            for field in field_names:
                self.assertIn(field, item)

    def assertFirstLineStartsWith(self, lines, beginning):
        self.assertTrue(lines[0].startswith(beginning),
                        msg=('Beginning of first line has invalid content: %s'
                             % lines[:3]))


class CommandFailed(subprocess.CalledProcessError):
    # adds output attribute for python2.6
    def __init__(self, returncode, cmd, output, stderr=""):
        super(CommandFailed, self).__init__(returncode, cmd)
        self.output = output
        self.stderr = stderr
