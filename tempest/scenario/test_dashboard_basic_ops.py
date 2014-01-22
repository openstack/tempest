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

import urllib
import urllib2

from lxml import html

from tempest.scenario import manager
from tempest.test import services


class TestDashboardBasicOps(manager.OfficialClientTest):

    """
    This is a basic scenario test:
    * checks that the login page is available
    * logs in as a regular user
    * checks that the user home page loads without error
    """

    @classmethod
    def setUpClass(cls):
        cls.set_network_resources()
        super(TestDashboardBasicOps, cls).setUpClass()

        if not cls.config.service_available.horizon:
            raise cls.skipException("Horizon support is required")

    def check_login_page(self):
        response = urllib2.urlopen(self.config.dashboard.dashboard_url)
        self.assertIn("<h3>Log In</h3>", response.read())

    def user_login(self):
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = self.opener.open(self.config.dashboard.dashboard_url).read()

        # Grab the CSRF token and default region
        csrf_token = html.fromstring(response).xpath(
            '//input[@name="csrfmiddlewaretoken"]/@value')[0]
        region = html.fromstring(response).xpath(
            '//input[@name="region"]/@value')[0]

        # Prepare login form request
        req = urllib2.Request(self.config.dashboard.login_url)
        req.add_header('Content-type', 'application/x-www-form-urlencoded')
        req.add_header('Referer', self.config.dashboard.dashboard_url)
        params = {'username': self.config.identity.username,
                  'password': self.config.identity.password,
                  'region': region,
                  'csrfmiddlewaretoken': csrf_token}
        self.opener.open(req, urllib.urlencode(params))

    def check_home_page(self):
        response = self.opener.open(self.config.dashboard.dashboard_url)
        self.assertIn('Overview', response.read())

    @services('dashboard')
    def test_basic_scenario(self):
        self.check_login_page()
        self.user_login()
        self.check_home_page()
