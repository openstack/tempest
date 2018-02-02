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

from oslo_log import log as logging
import six

from tempest.lib import base
import tempest.lib.cli.output_parser
from tempest.lib import exceptions


LOG = logging.getLogger(__name__)


def execute(cmd, action, flags='', params='', fail_ok=False,
            merge_stderr=False, cli_dir='/usr/bin', prefix=''):
    """Executes specified command for the given action.

    :param cmd: command to be executed
    :type cmd: string
    :param action: string of the cli command to run
    :type action: string
    :param flags: any optional cli flags to use
    :type flags: string
    :param params: string of any optional positional args to use
    :type params: string
    :param fail_ok: boolean if True an exception is not raised when the
                    cli return code is non-zero
    :type fail_ok: boolean
    :param merge_stderr: boolean if True the stderr buffer is merged into
                         stdout
    :type merge_stderr: boolean
    :param cli_dir: The path where the cmd can be executed
    :type cli_dir: string
    :param prefix: prefix to insert before command
    :type prefix: string
    """
    cmd = ' '.join([prefix, os.path.join(cli_dir, cmd),
                    flags, action, params])
    cmd = cmd.strip()
    LOG.info("running: '%s'", cmd)
    if six.PY2:
        cmd = cmd.encode('utf-8')
    cmd = shlex.split(cmd)
    stdout = subprocess.PIPE
    stderr = subprocess.STDOUT if merge_stderr else subprocess.PIPE
    proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
    result, result_err = proc.communicate()
    if not fail_ok and proc.returncode != 0:
        raise exceptions.CommandFailed(proc.returncode,
                                       cmd,
                                       result,
                                       result_err)
    if six.PY2:
        return result
    else:
        return os.fsdecode(result)


class CLIClient(object):
    """Class to use OpenStack official python client CLI's with auth

    :param username: The username to authenticate with
    :type username: string
    :param password: The password to authenticate with
    :type password: string
    :param tenant_name: The name of the tenant to use with the client calls
    :type tenant_name: string
    :param uri: The auth uri for the OpenStack Deployment
    :type uri: string
    :param cli_dir: The path where the python client binaries are installed.
                    defaults to /usr/bin
    :type cli_dir: string
    :param insecure: if True, --insecure is passed to python client binaries.
    :type insecure: boolean
    :param prefix: prefix to insert before commands
    :type prefix: string
    :param user_domain_name: User's domain name
    :type user_domain_name: string
    :param user_domain_id: User's domain ID
    :type user_domain_id: string
    :param project_domain_name: Project's domain name
    :type project_domain_name: string
    :param project_domain_id: Project's domain ID
    :type project_domain_id: string
    :param identity_api_version: Version of the Identity API
    :type identity_api_version: string
    """

    def __init__(self, username='', password='', tenant_name='', uri='',
                 cli_dir='', insecure=False, prefix='', user_domain_name=None,
                 user_domain_id=None, project_domain_name=None,
                 project_domain_id=None, identity_api_version=None, *args,
                 **kwargs):
        """Initialize a new CLIClient object."""
        super(CLIClient, self).__init__()
        self.cli_dir = cli_dir if cli_dir else '/usr/bin'
        self.username = username
        self.tenant_name = tenant_name
        self.password = password
        self.uri = uri
        self.insecure = insecure
        self.prefix = prefix
        self.user_domain_name = user_domain_name
        self.user_domain_id = user_domain_id
        self.project_domain_name = project_domain_name
        self.project_domain_id = project_domain_id
        self.identity_api_version = identity_api_version

    def nova(self, action, flags='', params='', fail_ok=False,
             endpoint_type='publicURL', merge_stderr=False):
        """Executes nova command for the given action.

        :param action: the cli command to run using nova
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        flags += ' --os-endpoint-type %s' % endpoint_type
        return self.cmd_with_auth(
            'nova', action, flags, params, fail_ok, merge_stderr)

    def nova_manage(self, action, flags='', params='', fail_ok=False,
                    merge_stderr=False):
        """Executes nova-manage command for the given action.

        :param action: the cli command to run using nova-manage
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        return execute(
            'nova-manage', action, flags, params, fail_ok, merge_stderr,
            self.cli_dir)

    def keystone(self, action, flags='', params='', fail_ok=False,
                 merge_stderr=False):
        """Executes keystone command for the given action.

        :param action: the cli command to run using keystone
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        return self.cmd_with_auth(
            'keystone', action, flags, params, fail_ok, merge_stderr)

    def glance(self, action, flags='', params='', fail_ok=False,
               endpoint_type='publicURL', merge_stderr=False):
        """Executes glance command for the given action.

        :param action: the cli command to run using glance
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        flags += ' --os-endpoint-type %s' % endpoint_type
        return self.cmd_with_auth(
            'glance', action, flags, params, fail_ok, merge_stderr)

    def ceilometer(self, action, flags='', params='',
                   fail_ok=False, endpoint_type='publicURL',
                   merge_stderr=False):
        """Executes ceilometer command for the given action.

        :param action: the cli command to run using ceilometer
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        flags += ' --os-endpoint-type %s' % endpoint_type
        return self.cmd_with_auth(
            'ceilometer', action, flags, params, fail_ok, merge_stderr)

    def heat(self, action, flags='', params='',
             fail_ok=False, endpoint_type='publicURL', merge_stderr=False):
        """Executes heat command for the given action.

        :param action: the cli command to run using heat
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        flags += ' --os-endpoint-type %s' % endpoint_type
        return self.cmd_with_auth(
            'heat', action, flags, params, fail_ok, merge_stderr)

    def cinder(self, action, flags='', params='', fail_ok=False,
               endpoint_type='publicURL', merge_stderr=False):
        """Executes cinder command for the given action.

        :param action: the cli command to run using cinder
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        flags += ' --endpoint-type %s' % endpoint_type
        return self.cmd_with_auth(
            'cinder', action, flags, params, fail_ok, merge_stderr)

    def swift(self, action, flags='', params='', fail_ok=False,
              endpoint_type='publicURL', merge_stderr=False):
        """Executes swift command for the given action.

        :param action: the cli command to run using swift
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        flags += ' --os-endpoint-type %s' % endpoint_type
        return self.cmd_with_auth(
            'swift', action, flags, params, fail_ok, merge_stderr)

    def neutron(self, action, flags='', params='', fail_ok=False,
                endpoint_type='publicURL', merge_stderr=False):
        """Executes neutron command for the given action.

        :param action: the cli command to run using neutron
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        flags += ' --endpoint-type %s' % endpoint_type
        return self.cmd_with_auth(
            'neutron', action, flags, params, fail_ok, merge_stderr)

    def sahara(self, action, flags='', params='',
               fail_ok=False, endpoint_type='publicURL', merge_stderr=True):
        """Executes sahara command for the given action.

        :param action: the cli command to run using sahara
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        flags += ' --endpoint-type %s' % endpoint_type
        return self.cmd_with_auth(
            'sahara', action, flags, params, fail_ok, merge_stderr)

    def openstack(self, action, flags='', params='', fail_ok=False,
                  merge_stderr=False):
        """Executes openstack command for the given action.

        :param action: the cli command to run using openstack
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        return self.cmd_with_auth(
            'openstack', action, flags, params, fail_ok, merge_stderr)

    def cmd_with_auth(self, cmd, action, flags='', params='',
                      fail_ok=False, merge_stderr=False):
        """Executes given command with auth attributes appended.

        :param cmd: command to be executed
        :type cmd: string
        :param action: command on cli to run
        :type action: string
        :param flags: optional cli flags to use
        :type flags: string
        :param params: optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the cli return
                        code is non-zero
        :type fail_ok: boolean
        :param merge_stderr:  if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        """
        creds = ('--os-username %s --os-project-name %s --os-password %s '
                 '--os-auth-url %s' %
                 (self.username,
                  self.tenant_name,
                  self.password,
                  self.uri))
        if self.identity_api_version:
            creds += ' --os-identity-api-version %s' % (
                self.identity_api_version)
        if self.user_domain_name is not None:
            creds += ' --os-user-domain-name %s' % self.user_domain_name
        if self.user_domain_id is not None:
            creds += ' --os-user-domain-id %s' % self.user_domain_id
        if self.project_domain_name is not None:
            creds += ' --os-project-domain-name %s' % self.project_domain_name
        if self.project_domain_id is not None:
            creds += ' --os-project-domain-id %s' % self.project_domain_id
        if self.insecure:
            flags = creds + ' --insecure ' + flags
        else:
            flags = creds + ' ' + flags
        return execute(cmd, action, flags, params, fail_ok, merge_stderr,
                       self.cli_dir, prefix=self.prefix)


class ClientTestBase(base.BaseTestCase):
    """Base test class for testing the OpenStack client CLI interfaces."""

    def setUp(self):
        super(ClientTestBase, self).setUp()
        self.clients = self._get_clients()
        self.parser = tempest.lib.cli.output_parser

    def _get_clients(self):
        """Abstract method to initialize CLIClient object.

        This method must be overloaded in child test classes. It should be
        used to initialize the CLIClient object with the appropriate
        credentials during the setUp() phase of tests.
        """
        raise NotImplementedError

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
