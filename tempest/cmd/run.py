# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Runs tempest tests

This command is used for running the tempest tests

Test Selection
==============
Tempest run has several options:

 * **--regex/-r**: This is a selection regex like what testr uses. It will run
                   any tests that match on re.match() with the regex
 * **--smoke**: Run all the tests tagged as smoke

There are also the **--blacklist_file** and **--whitelist_file** options that
let you pass a filepath to tempest run with the file format being a line
separated regex, with '#' used to signify the start of a comment on a line.
For example::

    # Regex file
    ^regex1 # Match these tests
    .*regex2 # Match those tests

The blacklist file will be used to construct a negative lookahead regex and
the whitelist file will simply OR all the regexes in the file. The whitelist
and blacklist file options are mutually exclusive so you can't use them
together. However, you can combine either with a normal regex or the *--smoke*
flag. When used with a blacklist file the generated regex will be combined to
something like::

    ^((?!black_regex1|black_regex2).)*$cli_regex1

When combined with a whitelist file all the regexes from the file and the CLI
regexes will be ORed.

You can also use the **--list-tests** option in conjunction with selection
arguments to list which tests will be run.

Test Execution
==============
There are several options to control how the tests are executed. By default
tempest will run in parallel with a worker for each CPU present on the machine.
If you want to adjust the number of workers use the **--concurrency** option
and if you want to run tests serially use **--serial**

Running with Workspaces
-----------------------
Tempest run enables you to run your tempest tests from any setup tempest
workspace it relies on you having setup a tempest workspace with either the
``tempest init`` or ``tempest workspace`` commands. Then using the
``--workspace`` CLI option you can specify which one of your workspaces you
want to run tempest from. Using this option you don't have to run Tempest
directly with you current working directory being the workspace, Tempest will
take care of managing everything to be executed from there.

Running from Anywhere
---------------------
Tempest run provides you with an option to execute tempest from anywhere on
your system. You are required to provide a config file in this case with the
``--config-file`` option. When run tempest will create a .testrepository
directory and a .testr.conf file in your current working directory. This way
you can use testr commands directly to inspect the state of the previous run.

Test Output
===========
By default tempest run's output to STDOUT will be generated using the
subunit-trace output filter. But, if you would prefer a subunit v2 stream be
output to STDOUT use the **--subunit** flag

"""

import io
import os
import sys
import threading

from cliff import command
from os_testr import regex_builder
from os_testr import subunit_trace
from testrepository.commands import run_argv

from tempest.cmd import init
from tempest.cmd import workspace
from tempest import config


CONF = config.CONF


class TempestRun(command.Command):

    def _set_env(self, config_file=None):
        if config_file:
            CONF.set_config_path(os.path.abspath(config_file))
        # NOTE(mtreinish): This is needed so that testr doesn't gobble up any
        # stacktraces on failure.
        if 'TESTR_PDB' in os.environ:
            return
        else:
            os.environ["TESTR_PDB"] = ""

    def _create_testrepository(self):
        if not os.path.isdir('.testrepository'):
            returncode = run_argv(['testr', 'init'], sys.stdin, sys.stdout,
                                  sys.stderr)
            if returncode:
                sys.exit(returncode)

    def _create_testr_conf(self):
        top_level_path = os.path.dirname(os.path.dirname(__file__))
        discover_path = os.path.join(top_level_path, 'test_discover')
        file_contents = init.TESTR_CONF % (top_level_path, discover_path)
        with open('.testr.conf', 'w+') as testr_conf_file:
                testr_conf_file.write(file_contents)

    def take_action(self, parsed_args):
        returncode = 0
        if parsed_args.config_file:
            self._set_env(parsed_args.config_file)
        else:
            self._set_env()
        # Workspace execution mode
        if parsed_args.workspace:
            workspace_mgr = workspace.WorkspaceManager(
                parsed_args.workspace_path)
            path = workspace_mgr.get_workspace(parsed_args.workspace)
            os.chdir(path)
            # NOTE(mtreinish): tempest init should create a .testrepository dir
            # but since workspaces can be imported let's sanity check and
            # ensure that one is created
            self._create_testrepository()
        # Local execution mode
        elif os.path.isfile('.testr.conf'):
            # If you're running in local execution mode and there is not a
            # testrepository dir create one
            self._create_testrepository()
        # local execution with config file mode
        elif parsed_args.config_file:
            self._create_testr_conf()
            self._create_testrepository()
        else:
            print("No .testr.conf file was found for local execution")
            sys.exit(2)

        regex = self._build_regex(parsed_args)
        if parsed_args.list_tests:
            argv = ['tempest', 'list-tests', regex]
            returncode = run_argv(argv, sys.stdin, sys.stdout, sys.stderr)
        else:
            options = self._build_options(parsed_args)
            returncode = self._run(regex, options)
        sys.exit(returncode)

    def get_description(self):
        return 'Run tempest'

    def get_parser(self, prog_name):
        parser = super(TempestRun, self).get_parser(prog_name)
        parser = self._add_args(parser)
        return parser

    def _add_args(self, parser):
        # workspace args
        parser.add_argument('--workspace', default=None,
                            help='Name of tempest workspace to use for running'
                                 ' tests. You can see a list of workspaces '
                                 'with tempest workspace list')
        parser.add_argument('--workspace-path', default=None,
                            dest='workspace_path',
                            help="The path to the workspace file, the default "
                                 "is ~/.tempest/workspace.yaml")
        # Configuration flags
        parser.add_argument('--config-file', default=None, dest='config_file',
                            help='Configuration file to run tempest with')
        # test selection args
        regex = parser.add_mutually_exclusive_group()
        regex.add_argument('--smoke', action='store_true',
                           help="Run the smoke tests only")
        regex.add_argument('--regex', '-r', default='',
                           help='A normal testr selection regex used to '
                                'specify a subset of tests to run')
        list_selector = parser.add_mutually_exclusive_group()
        list_selector.add_argument('--whitelist_file',
                                   help="Path to a whitelist file, this file "
                                        "contains a separate regex on each "
                                        "newline.")
        list_selector.add_argument('--blacklist_file',
                                   help='Path to a blacklist file, this file '
                                        'contains a separate regex exclude on '
                                        'each newline')
        # list only args
        parser.add_argument('--list-tests', '-l', action='store_true',
                            help='List tests',
                            default=False)
        # execution args
        parser.add_argument('--concurrency', '-w',
                            help="The number of workers to use, defaults to "
                                 "the number of cpus")
        parallel = parser.add_mutually_exclusive_group()
        parallel.add_argument('--parallel', dest='parallel',
                              action='store_true',
                              help='Run tests in parallel (this is the'
                                   ' default)')
        parallel.add_argument('--serial', dest='parallel',
                              action='store_false',
                              help='Run tests serially')
        # output args
        parser.add_argument("--subunit", action='store_true',
                            help='Enable subunit v2 output')

        parser.set_defaults(parallel=True)
        return parser

    def _build_regex(self, parsed_args):
        regex = ''
        if parsed_args.smoke:
            regex = 'smoke'
        elif parsed_args.regex:
            regex = parsed_args.regex
        if parsed_args.whitelist_file or parsed_args.blacklist_file:
            regex = regex_builder.construct_regex(parsed_args.blacklist_file,
                                                  parsed_args.whitelist_file,
                                                  regex, False)
        return regex

    def _build_options(self, parsed_args):
        options = []
        if parsed_args.subunit:
            options.append("--subunit")
        if parsed_args.parallel:
            options.append("--parallel")
        if parsed_args.concurrency:
            options.append("--concurrency=%s" % parsed_args.concurrency)
        return options

    def _run(self, regex, options):
        returncode = 0
        argv = ['tempest', 'run', regex] + options
        if '--subunit' in options:
            returncode = run_argv(argv, sys.stdin, sys.stdout, sys.stderr)
        else:
            argv.append('--subunit')
            stdin = io.StringIO()
            stdout_r, stdout_w = os.pipe()
            subunit_w = os.fdopen(stdout_w, 'wt')
            subunit_r = os.fdopen(stdout_r)
            returncodes = {}

            def run_argv_thread():
                returncodes['testr'] = run_argv(argv, stdin, subunit_w,
                                                sys.stderr)
                subunit_w.close()

            run_thread = threading.Thread(target=run_argv_thread)
            run_thread.start()
            returncodes['subunit-trace'] = subunit_trace.trace(subunit_r,
                                                               sys.stdout)
            run_thread.join()
            subunit_r.close()
            # python version of pipefail
            if returncodes['testr']:
                returncode = returncodes['testr']
            elif returncodes['subunit-trace']:
                returncode = returncodes['subunit-trace']
        return returncode
