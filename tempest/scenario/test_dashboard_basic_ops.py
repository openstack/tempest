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

from six.moves import html_parser as HTMLParser
from six.moves.urllib import parse
from six.moves.urllib import request

from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF


class HorizonHTMLParser(HTMLParser.HTMLParser):
    csrf_token = None
    region = None
    login = None

    def _find_name(self, attrs, name):
        for attrpair in attrs:
            if attrpair[0] == 'name' and attrpair[1] == name:
                return True
        return False

    def _find_value(self, attrs):
        for attrpair in attrs:
            if attrpair[0] == 'value':
                return attrpair[1]
        return None

    def _find_attr_value(self, attrs, attr_name):
        for attrpair in attrs:
            if attrpair[0] == attr_name:
                return attrpair[1]
        return None

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            if self._find_name(attrs, 'csrfmiddlewaretoken'):
                self.csrf_token = self._find_value(attrs)
            if self._find_name(attrs, 'region'):
                self.region = self._find_value(attrs)
        if tag == 'form':
            self.login = self._find_attr_value(attrs, 'action')


class TestDashboardBasicOps(manager.ScenarioTest):

    """The test suite for dashboard basic operations

    This is a basic scenario test:
    * checks that the login page is available
    * logs in as a regular user
    * checks that the user home page loads without error
    """

    @classmethod
    def skip_checks(cls):
        super(TestDashboardBasicOps, cls).skip_checks()
        if not CONF.service_available.horizon:
            raise cls.skipException("Horizon support is required")

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(TestDashboardBasicOps, cls).setup_credentials()

    def check_login_page(self):
        response = request.urlopen(CONF.dashboard.dashboard_url)
        self.assertIn("id_username", response.read())

    def user_login(self, username, password):
        self.opener = request.build_opener(request.HTTPCookieProcessor())
        response = self.opener.open(CONF.dashboard.dashboard_url).read()

        # Grab the CSRF token and default region
        parser = HorizonHTMLParser()
        parser.feed(response)

        # construct login url for dashboard, discovery accommodates non-/ web
        # root for dashboard
        login_url = parse.urljoin(CONF.dashboard.dashboard_url, parser.login)

        # Prepare login form request
        req = request.Request(login_url)
        req.add_header('Content-type', 'application/x-www-form-urlencoded')
        req.add_header('Referer', CONF.dashboard.dashboard_url)

        # Pass the default domain name regardless of the auth version in order
        # to test the scenario of when horizon is running with keystone v3
        params = {'username': username,
                  'password': password,
                  'region': parser.region,
                  'domain': CONF.auth.default_credentials_domain_name,
                  'csrfmiddlewaretoken': parser.csrf_token}
        self.opener.open(req, parse.urlencode(params))

    def check_home_page(self):
        response = self.opener.open(CONF.dashboard.dashboard_url)
        self.assertIn('Overview', response.read())

    @test.idempotent_id('4f8851b1-0e69-482b-b63b-84c6e76f6c80')
    @test.services('dashboard')
    def test_basic_scenario(self):
        creds = self.os.credentials
        self.check_login_page()
        self.user_login(creds.username, creds.password)
        self.check_home_page()
