===================================
How To Implement Microversion Tests
===================================

Tempest provides stable interfaces to test API Microversion.
For Details, see: `API Microversion testing Framework`_
This document explains how to implement Microversion tests using those
interfaces.

.. _API Microversion testing Framework: http://docs.openstack.org/developer/tempest/library/api_microversion_testing.html


Configuration options for Microversion
""""""""""""""""""""""""""""""""""""""

* Add configuration options for specifying test target Microversions.
  We need to specify test target Microversions because the supported
  Microversions may be different between OpenStack clouds. For operating
  multiple Microversion tests in a single Tempest operation, configuration
  options should represent the range of test target Microversions.
  New configuration options are:
  * min_microversion
  * max_microversion

  Those should be defined under respective section of each service.
  For example::
      [compute]
      min_microversion = None
      max_microversion = latest


How To Implement Microversion Tests
"""""""""""""""""""""""""""""""""""

Step1: Add skip logic based on configured Microversion range
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Add logic to skip the tests based on Tests class and configured Microversion
range.
api_version_utils.check_skip_with_microversion function can be used
to automatically skip the tests which do not fall under configured
Microversion range.
For example::

    class BaseTestCase1(api_version_utils.BaseMicroversionTest):

        [..]
    @classmethod
    def skip_checks(cls):
        super(BaseTestCase1, cls).skip_checks()
        api_version_utils.check_skip_with_microversion(cls.min_microversion,
                                                       cls.max_microversion,
                                                       CONF.compute.min_microversion,
                                                       CONF.compute.max_microversion)

Skip logic can be added in tests base class or any specific test class depends on
tests class structure.

Step2: Selected API request microversion
''''''''''''''''''''''''''''''''''''''''

Select appropriate Microversion which needs to be used
to send with API request.
api_version_utils.select_request_microversion function can be used
to select the appropriate Microversion which will be used for API request.
For example::

    @classmethod
    def resource_setup(cls):
        super(BaseTestCase1, cls).resource_setup()
        cls.request_microversion = (
            api_version_utils.select_request_microversion(
                cls.min_microversion,
                CONF.compute.min_microversion))


Step3: Set Microversion on Service Clients
''''''''''''''''''''''''''''''''''''''''''

Microversion selected by Test Class in previous step needs to be set on
service clients so that APIs can be requested with selected Microversion.

Microversion can be defined as global variable on service clients which
can be set using fixture.
Also Microversion header name needs to be defined on service clients which
should be constant because it is not supposed to be changed by project
as per API contract.
For example::

      COMPUTE_MICROVERSION = None

      class BaseClient1(rest_client.RestClient):
          api_microversion_header_name = 'X-OpenStack-Nova-API-Version'

Now test class can set the selected Microversion on required service clients
using fixture which can take care of resetting the same once tests is completed.
For example::

    def setUp(self):
        super(BaseTestCase1, self).setUp()
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            self.request_microversion))

Service clients needs to add set Microversion in API request header which
can be done by overriding the get_headers() method of rest_client.
For example::

      COMPUTE_MICROVERSION = None

      class BaseClient1(rest_client.RestClient):
          api_microversion_header_name = 'X-OpenStack-Nova-API-Version'

          def get_headers(self):
              headers = super(BaseClient1, self).get_headers()
              if COMPUTE_MICROVERSION:
                  headers[self.api_microversion_header_name] = COMPUTE_MICROVERSION
              return headers


Step4: Separate Test classes for each Microversion
''''''''''''''''''''''''''''''''''''''''''''''''''

This is last step to implement Microversion test class.

For any Microversion tests, basically we need to implement a
separate test class. In addition, each test class defines its
Microversion range with class variable like min_microversion
and max_microversion. Tests will be valid for that defined range.
If that range is out of configured Microversion range then, test
will be skipped.

*NOTE: Microversion testing is supported at test class level not at individual
test case level.*
For example:

Below test is applicable for Microversion from 2.2 till 2.9::

    class BaseTestCase1(api_version_utils.BaseMicroversionTest,
                        tempest.test.BaseTestCase):

        [..]


    class Test1(BaseTestCase1):
        min_microversion = '2.2'
        max_microversion = '2.9'

        [..]

Below test is applicable for Microversion from 2.10 till latest::

    class Test2(BaseTestCase1):
        min_microversion = '2.10'
        max_microversion = 'latest'

        [..]




Notes about Compute Microversion Tests
"""""""""""""""""""""""""""""""""""
Some of the compute Microversion tests have been already implemented
with the Microversion testing framework. So for further tests only
step 4 is needed.

Along with that JSON response schema might need versioning if needed.

Compute service clients strictly validate the response against defined JSON
schema and does not allow additional elements in response.
So if that Microversion changed the API response then schema needs to be versioned.
New JSON schema file needs to be defined with new response attributes and service
client methods will select the schema based on requested microversion.

If Microversion tests are implemented randomly meaning not
in sequence order(v2.20 tests added and previous Microversion tests are not yet added)
then, still schema might need to be version for older Microversion if they changed
the response.
This is because Nova Microversion includes all the previous Microversions behavior.

For Example:
    Implementing the v2.20 Microversion tests before v2.9 and 2.19-
    v2.20 API request will respond as latest behavior of Nova till v2.20,
    and in v2.9 and 2.19, server response has been changed so response schema needs
    to be versioned accordingly.

That can be done by using the get_schema method in below module:

The base_compute_client module
''''''''''''''''''''''''''''''

.. automodule:: tempest.lib.services.compute.base_compute_client
   :members:


Microversion tests implemented in Tempest
"""""""""""""""""""""""""""""""""""""""""

* Compute

 * `2.1`_

 .. _2.1:  http://docs.openstack.org/developer/nova/api_microversion_history.html#id1

 * `2.2`_

 .. _2.2: http://docs.openstack.org/developer/nova/api_microversion_history.html#id2

 * `2.10`_

 .. _2.10: http://docs.openstack.org/developer/nova/api_microversion_history.html#id9
