# Copyright 2015 Dell Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.

import sys

from cliff import app
from cliff import commandmanager
from oslo_log import log as logging
from pbr import version


class Main(app.App):

    log = logging.getLogger(__name__)

    def __init__(self):
        super(Main, self).__init__(
            description='Tempest cli application',
            version=version.VersionInfo('tempest').version_string_with_vcs(),
            command_manager=commandmanager.CommandManager('tempest.cm'),
            deferred_help=True,
            )

    def initialize_app(self, argv):
        self.log.debug('tempest initialize_app')

    def prepare_to_run_command(self, cmd):
        self.log.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.log.debug('tempest clean_up %s', cmd.__class__.__name__)
        if err:
            self.log.debug('tempest got an error: %s', err)


def main(argv=sys.argv[1:]):
    the_app = Main()
    return the_app.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
