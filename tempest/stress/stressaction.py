# vim: tabstop=4 shiftwidth=4 softtabstop=4

# (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import signal
import sys


class StressAction(object):

    def __init__(self, manager, logger):
        self.manager = manager
        self.logger = logger
        self.runs = 0

    def _shutdown_handler(self, signal, frame):
        self.tearDown()
        sys.exit(0)

    def setUp(self, **kwargs):
        """This method is called before the run method
        to help the test initiatlize any structures.
        kwargs contains arguments passed in from the
        configuration json file.

        setUp doesn't count against the time duration.
        """
        self.logger.debug("setUp")

    def tearDown(self):
        """This method is called to do any cleanup
        after the test is complete.
        """
        self.logger.debug("tearDown")

    def execute(self):
        """This is the main execution entry point called
        by the driver.   We register a signal handler to
        allow us to gracefull tearDown, and then exit.
        We also keep track of how many runs we do.
        """
        signal.signal(signal.SIGHUP, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        while True:
            self.run()
            self.runs = self.runs + 1

    def run(self):
        """This method is where the stress test code runs."""
        raise NotImplemented()
