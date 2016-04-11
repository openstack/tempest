#    Copyright 2016 OpenStack Foundation
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
#


def generate_timeout_series(timeout):
    """Generate a series of times that exceeds the given timeout.

    Yields a series of fake time.time() floating point numbers
    such that the difference between each pair in the series just
    exceeds the timeout value that is passed in.  Useful for
    mocking time.time() in methods that otherwise wait for timeout
    seconds.
    """
    iteration = 0
    while True:
        iteration += 1
        yield (iteration * timeout) + iteration
