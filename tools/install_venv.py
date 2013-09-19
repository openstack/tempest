# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# flake8: noqa
# Copyright 2010 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

"""Installation script for Tempest's development virtualenv."""

import os
import sys

import install_venv_common as install_venv


class CentOS(install_venv.Fedora):
    """This covers CentOS."""

    def post_process(self):
        if not self.check_pkg('openssl-devel'):
            self.yum.install('openssl-devel', check_exit_code=False)


def print_help():
    """This prints Help."""

    help = """
    Tempest development environment setup is complete.

    Tempest development uses virtualenv to track and manage Python dependencies
    while in development and testing.

    To activate the Tempest virtualenv for the extent of your current shell
    session you can run:

    $ source .venv/bin/activate

    Or, if you prefer, you can run commands in the virtualenv on a case by case
    basis by running:

    $ tools/with_venv.sh <your command>

    Also, make test will automatically use the virtualenv.
    """
    print(help)


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    venv = os.path.join(root, '.venv')
    pip_requires = os.path.join(root, 'requirements.txt')
    test_requires = os.path.join(root, 'test-requirements.txt')
    py_version = "python%s.%s" % (sys.version_info[0], sys.version_info[1])
    project = 'Tempest'
    install = install_venv.InstallVenv(root, venv, pip_requires, test_requires,
                                       py_version, project)
    if os.path.exists('/etc/redhat-release'):
        with open('/etc/redhat-release') as rh_release:
            if 'CentOS' in rh_release.read():
                install_venv.Fedora = CentOS
    options = install.parse_args(argv)
    install.check_python_version()
    install.check_dependencies()
    install.create_virtualenv(no_site_packages=options.no_site_packages)
    install.install_dependencies()
    install.post_process()
    print_help()

if __name__ == '__main__':
    main(sys.argv)
