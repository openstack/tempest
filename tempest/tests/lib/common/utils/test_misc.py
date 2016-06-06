# Copyright 2014 NEC Corporation.
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


from tempest.lib.common.utils import misc
from tempest.tests import base


@misc.singleton
class TestFoo(object):

    count = 0

    def increment(self):
        self.count += 1
        return self.count


@misc.singleton
class TestBar(object):

    count = 0

    def increment(self):
        self.count += 1
        return self.count


class TestMisc(base.TestCase):

    def test_singleton(self):
        test = TestFoo()
        self.assertEqual(0, test.count)
        self.assertEqual(1, test.increment())
        test2 = TestFoo()
        self.assertEqual(1, test.count)
        self.assertEqual(1, test2.count)
        self.assertEqual(test, test2)
        test3 = TestBar()
        self.assertNotEqual(test, test3)
