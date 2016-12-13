# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import shutil
import subprocess
import sys

from cliff import command
from oslo_config import generator
from oslo_log import log as logging
from six import moves

from tempest.cmd.workspace import WorkspaceManager

LOG = logging.getLogger(__name__)

TESTR_CONF = """[DEFAULT]
test_command=OS_STDOUT_CAPTURE=${OS_STDOUT_CAPTURE:-1} \\
    OS_STDERR_CAPTURE=${OS_STDERR_CAPTURE:-1} \\
    OS_TEST_TIMEOUT=${OS_TEST_TIMEOUT:-500} \\
    ${PYTHON:-python} -m subunit.run discover -t %s %s $LISTOPT $IDOPTION
test_id_option=--load-list $IDFILE
test_list_option=--list
group_regex=([^\.]*\.)*
"""


def get_tempest_default_config_dir():
    """Get default config directory of tempest

    There are 3 dirs that get tried in priority order. First is /etc/tempest,
    if that doesn't exist it looks for a tempest dir in the XDG_CONFIG_HOME
    dir (defaulting to ~/.config/tempest) and last it tries for a
    ~/.tempest/etc directory. If none of these exist a ~/.tempest/etc
    directory will be created.

    :return: default config dir
    """
    global_conf_dir = '/etc/tempest'
    xdg_config = os.environ.get('XDG_CONFIG_HOME',
                                os.path.expanduser('~/.config'))
    user_xdg_global_path = os.path.join(xdg_config, 'tempest')
    user_global_path = os.path.join(os.path.expanduser('~'), '.tempest/etc')
    if os.path.isdir(global_conf_dir):
        return global_conf_dir
    elif os.path.isdir(user_xdg_global_path):
        return user_xdg_global_path
    elif os.path.isdir(user_global_path):
        return user_global_path
    else:
        os.makedirs(user_global_path)
        return user_global_path


class TempestInit(command.Command):
    """Setup a local working environment for running tempest"""

    def get_parser(self, prog_name):
        parser = super(TempestInit, self).get_parser(prog_name)
        parser.add_argument('dir', nargs='?', default=os.getcwd())
        parser.add_argument('--config-dir', '-c', default=None)
        parser.add_argument('--show-global-config-dir', '-s',
                            action='store_true', dest='show_global_dir',
                            help="Print the global config dir location, "
                                 "then exit")
        parser.add_argument('--name', help="The workspace name", default=None)
        parser.add_argument('--workspace-path', default=None,
                            help="The path to the workspace file, the default "
                                 "is ~/.tempest/workspace")
        return parser

    def generate_testr_conf(self, local_path):
        testr_conf_path = os.path.join(local_path, '.testr.conf')
        top_level_path = os.path.dirname(os.path.dirname(__file__))
        discover_path = os.path.join(top_level_path, 'test_discover')
        testr_conf = TESTR_CONF % (top_level_path, discover_path)
        with open(testr_conf_path, 'w+') as testr_conf_file:
            testr_conf_file.write(testr_conf)

    def update_local_conf(self, conf_path, lock_dir, log_dir):
        config_parse = moves.configparser.SafeConfigParser()
        config_parse.optionxform = str
        with open(conf_path, 'a+') as conf_file:
            # Set local lock_dir in tempest conf
            if not config_parse.has_section('oslo_concurrency'):
                config_parse.add_section('oslo_concurrency')
            config_parse.set('oslo_concurrency', 'lock_path', lock_dir)
            # Set local log_dir in tempest conf
            config_parse.set('DEFAULT', 'log_dir', log_dir)
            # Set default log filename to tempest.log
            config_parse.set('DEFAULT', 'log_file', 'tempest.log')
            config_parse.write(conf_file)

    def copy_config(self, etc_dir, config_dir):
        if os.path.isdir(config_dir):
            shutil.copytree(config_dir, etc_dir)
        else:
            LOG.warning("Global config dir %s can't be found" % config_dir)

    def generate_sample_config(self, local_dir):
        conf_generator = os.path.join(os.path.dirname(__file__),
                                      'config-generator.tempest.conf')
        output_file = os.path.join(local_dir, 'etc/tempest.conf.sample')
        if os.path.isfile(conf_generator):
            generator.main(['--config-file', conf_generator, '--output-file',
                            output_file])
        else:
            LOG.warning("Skipping sample config generation because global "
                        "config file %s can't be found" % conf_generator)

    def create_working_dir(self, local_dir, config_dir):
        # make sure we are working with abspath however tempest init is called
        local_dir = os.path.abspath(local_dir)
        # Create local dir if missing
        if not os.path.isdir(local_dir):
            LOG.debug('Creating local working dir: %s' % local_dir)
            os.mkdir(local_dir)
        elif not os.listdir(local_dir) == []:
            raise OSError("Directory you are trying to initialize already "
                          "exists and is not empty: %s" % local_dir)

        lock_dir = os.path.join(local_dir, 'tempest_lock')
        etc_dir = os.path.join(local_dir, 'etc')
        config_path = os.path.join(etc_dir, 'tempest.conf')
        log_dir = os.path.join(local_dir, 'logs')
        testr_dir = os.path.join(local_dir, '.testrepository')
        # Create lock dir
        if not os.path.isdir(lock_dir):
            LOG.debug('Creating lock dir: %s' % lock_dir)
            os.mkdir(lock_dir)
        # Create log dir
        if not os.path.isdir(log_dir):
            LOG.debug('Creating log dir: %s' % log_dir)
            os.mkdir(log_dir)
        # Create and copy local etc dir
        self.copy_config(etc_dir, config_dir)
        # Generate the sample config file
        self.generate_sample_config(local_dir)
        # Update local confs to reflect local paths
        self.update_local_conf(config_path, lock_dir, log_dir)
        # Generate a testr conf file
        self.generate_testr_conf(local_dir)
        # setup local testr working dir
        if not os.path.isdir(testr_dir):
            subprocess.call(['testr', 'init'], cwd=local_dir)

    def take_action(self, parsed_args):
        workspace_manager = WorkspaceManager(parsed_args.workspace_path)
        name = parsed_args.name or parsed_args.dir.split(os.path.sep)[-1]
        workspace_manager.register_new_workspace(
            name, parsed_args.dir, init=True)
        config_dir = parsed_args.config_dir or get_tempest_default_config_dir()
        if parsed_args.show_global_dir:
            print("Global config dir is located at: %s" % config_dir)
            sys.exit(0)
        self.create_working_dir(parsed_args.dir, config_dir)
