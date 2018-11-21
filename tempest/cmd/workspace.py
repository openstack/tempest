# Copyright 2016 Rackspace
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

"""
Manages Tempest workspaces

This command is used for managing tempest workspaces

Commands
========

list
----
Outputs the name and path of all known tempest workspaces

register
--------
Registers a new tempest workspace via a given ``--name`` and ``--path``

rename
------
Renames a tempest workspace from ``--old-name`` to ``--new-name``

move
----
Changes the path of a given tempest workspace ``--name`` to ``--path``

remove
------
Deletes the entry for a given tempest workspace ``--name``

``--rmdir`` Deletes the given tempest workspace directory

General Options
===============

* ``--workspace_path``: Allows the user to specify a different location for the
  workspace.yaml file containing the workspace definitions instead of
  ``~/.tempest/workspace.yaml``
"""

import os
import shutil
import sys

from cliff import command
from cliff import lister
from oslo_concurrency import lockutils
import yaml

from tempest import config

CONF = config.CONF


class WorkspaceManager(object):
    def __init__(self, path=None):
        lockutils.get_lock_path(CONF)
        self.path = path or os.path.join(
            os.path.expanduser("~"), ".tempest", "workspace.yaml")
        if not os.path.isdir(os.path.dirname(self.path)):
            os.makedirs(self.path.rsplit(os.path.sep, 1)[0])
        self.workspaces = {}

    @lockutils.synchronized('workspaces', external=True)
    def get_workspace(self, name):
        """Returns the workspace that has the given name

        If the workspace isn't registered then `None` is returned.
        """
        self._populate()
        return self.workspaces.get(name)

    @lockutils.synchronized('workspaces', external=True)
    def rename_workspace(self, old_name, new_name):
        self._populate()
        self._name_exists(old_name)
        self._invalid_name_check(new_name)
        self._workspace_name_exists(new_name)
        self.workspaces[new_name] = self.workspaces.pop(old_name)
        self._write_file()

    @lockutils.synchronized('workspaces', external=True)
    def move_workspace(self, name, path):
        self._populate()
        path = os.path.abspath(os.path.expanduser(path)) if path else path
        self._name_exists(name)
        self._validate_path(path)
        self.workspaces[name] = path
        self._write_file()

    def _name_exists(self, name):
        if name not in self.workspaces:
            print("A workspace was not found with name: {0}".format(name))
            sys.exit(1)

    @lockutils.synchronized('workspaces', external=True)
    def remove_workspace_entry(self, name):
        self._populate()
        self._name_exists(name)
        workspace_path = self.workspaces.pop(name)
        self._write_file()
        return workspace_path

    @lockutils.synchronized('workspaces', external=True)
    def remove_workspace_directory(self, workspace_path):
        self._validate_path(workspace_path)
        shutil.rmtree(workspace_path)

    @lockutils.synchronized('workspaces', external=True)
    def list_workspaces(self):
        self._populate()
        self._validate_workspaces()
        return self.workspaces

    def _workspace_name_exists(self, name):
        if name in self.workspaces:
            print("A workspace already exists with name: {0}.".format(
                name))
            sys.exit(1)

    def _invalid_name_check(self, name):
        if not name:
            print("None or empty name is specified."
                  " Please specify correct name for workspace.")
            sys.exit(1)

    def _validate_path(self, path):
        if not path:
            print("None or empty path is specified for workspace."
                  " Please specify correct workspace path.")
            sys.exit(1)
        if not os.path.exists(path):
            print("Path does not exist.")
            sys.exit(1)

    @lockutils.synchronized('workspaces', external=True)
    def register_new_workspace(self, name, path, init=False):
        """Adds the new workspace and writes out the new workspace config"""
        self._populate()
        path = os.path.abspath(os.path.expanduser(path)) if path else path
        # This only happens when register is called from outside of init
        if not init:
            self._validate_path(path)
        self._invalid_name_check(name)
        self._workspace_name_exists(name)
        self.workspaces[name] = path
        self._write_file()

    def _validate_workspaces(self):
        if self.workspaces is not None:
            self.workspaces = {n: p for n, p in self.workspaces.items()
                               if os.path.exists(p)}
            self._write_file()

    def _write_file(self):
        with open(self.path, 'w') as f:
            f.write(yaml.dump(self.workspaces))

    def _populate(self):
        if not os.path.isfile(self.path):
            return
        with open(self.path, 'r') as f:
            self.workspaces = yaml.safe_load(f) or {}


def add_global_arguments(parser):
    parser.add_argument(
        '--workspace-path', required=False, default=None,
        help="The path to the workspace file, the default is "
             "~/.tempest/workspace.yaml")
    return parser


class TempestWorkspaceRegister(command.Command):
    def get_description(self):
        return ('Registers a new tempest workspace via a given '
                '--name and --path')

    def get_parser(self, prog_name):
        parser = super(TempestWorkspaceRegister, self).get_parser(prog_name)
        add_global_arguments(parser)
        parser.add_argument('--name', required=True)
        parser.add_argument('--path', required=True)

        return parser

    def take_action(self, parsed_args):
        self.manager = WorkspaceManager(parsed_args.workspace_path)
        self.manager.register_new_workspace(parsed_args.name, parsed_args.path)
        sys.exit(0)


class TempestWorkspaceRename(command.Command):
    def get_description(self):
        return 'Renames a tempest workspace from --old-name to --new-name'

    def get_parser(self, prog_name):
        parser = super(TempestWorkspaceRename, self).get_parser(prog_name)
        add_global_arguments(parser)
        parser.add_argument('--old-name', required=True)
        parser.add_argument('--new-name', required=True)

        return parser

    def take_action(self, parsed_args):
        self.manager = WorkspaceManager(parsed_args.workspace_path)
        self.manager.rename_workspace(
            parsed_args.old_name, parsed_args.new_name)
        sys.exit(0)


class TempestWorkspaceMove(command.Command):
    def get_description(self):
        return 'Changes the path of a given tempest workspace --name to --path'

    def get_parser(self, prog_name):
        parser = super(TempestWorkspaceMove, self).get_parser(prog_name)
        add_global_arguments(parser)
        parser.add_argument('--name', required=True)
        parser.add_argument('--path', required=True)

        return parser

    def take_action(self, parsed_args):
        self.manager = WorkspaceManager(parsed_args.workspace_path)
        self.manager.move_workspace(parsed_args.name, parsed_args.path)
        sys.exit(0)


class TempestWorkspaceRemove(command.Command):
    def get_description(self):
        return 'Deletes the entry for a given tempest workspace --name'

    def get_parser(self, prog_name):
        parser = super(TempestWorkspaceRemove, self).get_parser(prog_name)
        add_global_arguments(parser)
        parser.add_argument('--name', required=True)
        parser.add_argument('--rmdir', action='store_true',
                            help='Deletes the given workspace directory')

        return parser

    def take_action(self, parsed_args):
        self.manager = WorkspaceManager(parsed_args.workspace_path)
        workspace_path = self.manager.remove_workspace_entry(parsed_args.name)
        if parsed_args.rmdir:
            self.manager.remove_workspace_directory(workspace_path)
        sys.exit(0)


class TempestWorkspaceList(lister.Lister):
    def get_description(self):
        return 'Outputs the name and path of all known tempest workspaces'

    def get_parser(self, prog_name):
        parser = super(TempestWorkspaceList, self).get_parser(prog_name)
        add_global_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        self.manager = WorkspaceManager(parsed_args.workspace_path)
        return (("Name", "Path"),
                ((n, p) for n, p in self.manager.list_workspaces().items()))
