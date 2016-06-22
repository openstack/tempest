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
Registers a new tempest workspace via a given --name and --path

rename
------
Renames a tempest workspace from --old-name to --new-name

move
----
Changes the path of a given tempest workspace --name to --path

remove
------
Deletes the entry for a given tempest workspace --name

General Options
===============

 **--workspace_path**: Allows the user to specify a different location for the
                       workspace.yaml file containing the workspace definitions
                       instead of ~/.tempest/workspace.yaml
"""

import os
import sys

from cliff import command
from oslo_concurrency import lockutils
import prettytable
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
        """Returns the workspace that has the given name"""
        self._populate()
        return self.workspaces.get(name)

    @lockutils.synchronized('workspaces', external=True)
    def rename_workspace(self, old_name, new_name):
        self._populate()
        self._name_exists(old_name)
        self._workspace_name_exists(new_name)
        self.workspaces[new_name] = self.workspaces.pop(old_name)
        self._write_file()

    @lockutils.synchronized('workspaces', external=True)
    def move_workspace(self, name, path):
        self._populate()
        path = os.path.abspath(os.path.expanduser(path))
        self._name_exists(name)
        self._validate_path(path)
        self.workspaces[name] = path
        self._write_file()

    def _name_exists(self, name):
        if name not in self.workspaces:
            print("A workspace was not found with name: {0}".format(name))
            sys.exit(1)

    @lockutils.synchronized('workspaces', external=True)
    def remove_workspace(self, name):
        self._populate()
        self._name_exists(name)
        self.workspaces.pop(name)
        self._write_file()

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

    def _validate_path(self, path):
        if not os.path.exists(path):
            print("Path does not exist.")
            sys.exit(1)

    @lockutils.synchronized('workspaces', external=True)
    def register_new_workspace(self, name, path, init=False):
        """Adds the new workspace and writes out the new workspace config"""
        self._populate()
        path = os.path.abspath(os.path.expanduser(path))
        # This only happens when register is called from outside of init
        if not init:
            self._validate_path(path)
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
            self.workspaces = yaml.load(f) or {}


class TempestWorkspace(command.Command):
    def take_action(self, parsed_args):
        self.manager = WorkspaceManager(parsed_args.workspace_path)
        if getattr(parsed_args, 'register', None):
            self.manager.register_new_workspace(
                parsed_args.name, parsed_args.path)
        elif getattr(parsed_args, 'rename', None):
            self.manager.rename_workspace(
                parsed_args.old_name, parsed_args.new_name)
        elif getattr(parsed_args, 'move', None):
            self.manager.move_workspace(
                parsed_args.name, parsed_args.path)
        elif getattr(parsed_args, 'remove', None):
            self.manager.remove_workspace(
                parsed_args.name)
        else:
            self._print_workspaces()
        sys.exit(0)

    def get_description(self):
        return 'Tempest workspace actions'

    def get_parser(self, prog_name):
        parser = super(TempestWorkspace, self).get_parser(prog_name)

        parser.add_argument(
            '--workspace-path', required=False, default=None,
            help="The path to the workspace file, the default is "
                 "~/.tempest/workspace.yaml")

        subparsers = parser.add_subparsers()

        list_parser = subparsers.add_parser('list')
        list_parser.set_defaults(list=True)

        register_parser = subparsers.add_parser('register')
        register_parser.add_argument('--name', required=True)
        register_parser.add_argument('--path', required=True)
        register_parser.set_defaults(register=True)

        update_parser = subparsers.add_parser('rename')
        update_parser.add_argument('--old-name', required=True)
        update_parser.add_argument('--new-name', required=True)
        update_parser.set_defaults(rename=True)

        move_parser = subparsers.add_parser('move')
        move_parser.add_argument('--name', required=True)
        move_parser.add_argument('--path', required=True)
        move_parser.set_defaults(move=True)

        remove_parser = subparsers.add_parser('remove')
        remove_parser.add_argument('--name', required=True)
        remove_parser.set_defaults(remove=True)

        return parser

    def _print_workspaces(self):
        output = prettytable.PrettyTable(["Name", "Path"])
        if self.manager.list_workspaces() is not None:
            for name, path in self.manager.list_workspaces().items():
                output.add_row([name, path])

        print(output)
