=================================
Microversion Testing With Tempest
=================================

Many OpenStack Services provide their APIs with `microversion`_
support and want to test them in Tempest.

.. _microversion: http://specs.openstack.org/openstack/api-wg/guidelines/microversion_specification.html

This document covers how to test microversions for each project and
whether tests should live in Tempest or on project side.

Tempest Scope For Microversion Testing
""""""""""""""""""""""""""""""""""""""
APIs microversions for any OpenStack service grow rapidly and
testing each and every microversion in Tempest is not feasible and
efficient way.
Also not every API microversion changes the complete system behavior
and many of them only change the API or DB layer to accept and return more
data on API.

Tempest is an integration test suite, but not all API microversion testing fall under this category.
As a result, Tempest mainly covers integration test cases for microversions, Other testing coverage
for microversion should be hosted on project side as functional tests or via Tempest plugin as per
project guidelines.

.. note:: Integration tests are those tests which involve more than one service to
     verify the expected behavior by single or combination of API requests.
     If a test is just to verify the API behavior as success and failure cases
     or verify its expected response object, then it does not fall under integration
     tests.

Tempest will cover only integration testing of applicable microversions with
below exceptions:

#. Test covers a feature which is important for interoperability. This covers tests requirement
   from Defcore.
#. Test needed to fill Schema gaps.
   Tempest validates API responses with defined JSON schema. API responses can be different on
   each microversion and the JSON schemas need to be defined separately for the microversion.
   While implementing new integration tests for a specific microversion, there
   may be a gap in the JSON schemas (caused by previous microversions) implemented
   in Tempest.
   Filling that gap while implementing the new integration test cases is not efficient due to
   many reasons:

   * Hard to review
   * Sync between multiple integration tests patches which try to fill the same schema gap at same
     time
   * Might delay the microversion change on project side where project team wants Tempest
     tests to verify the results.

   Tempest will allow to fill the schema gaps at the end of each cycle, or more
   often if required.
   Schema gap can be filled with testing those with a minimal set of tests. Those
   tests might not be integration tests and might be already covered on project
   side also.
   This exception is needed because:

   * Allow to create microversion response schema in Tempest at the same time that projects are
     implementing their API microversions. This will make implementation easier for adding
     required tests before a new microversion change can be merged in the corresponding project
     and hence accelerate the development of microversions.
   * New schema must be verified by at least one test case which exercises such schema.

   For example:
      If any projects implemented 4 API microversion say- v2.3, v2.4, v2.5, v2.6
      Assume microversion v2.3, v2.4, v2.6 change the API Response which means Tempest
      needs to add JSON schema for v2.3, v2.4, v2.6.
      In that case if only 1 or 2 tests can verify all new schemas then we do not need
      separate tests for each new schemas. In worst case, we have to add 3 separate tests.
#. Test covers service behavior at large scale with involvement of more deep layer like hypervisor
   etc not just API/DB layer. This type of tests will be added case by case basis and
   with project team consultation about why it cannot be covered on project side and worth to test
   in Tempest.

Project Scope For Microversion Testing
""""""""""""""""""""""""""""""""""""""
All microversions testing which are not covered under Tempest as per above section, should be
tested on project side as functional tests or as Tempest plugin as per project decision.


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
  For example:

  .. code-block:: ini

      [compute]
      min_microversion = None
      max_microversion = latest


How To Implement Microversion Tests
"""""""""""""""""""""""""""""""""""

Tempest provides stable interfaces to test API Microversion.
For Details, see: `API Microversion testing Framework`_
This document explains how to implement Microversion tests using those
interfaces.

.. _API Microversion testing Framework: https://docs.openstack.org/tempest/latest/library/api_microversion_testing.html


Step1: Add skip logic based on configured Microversion range
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Add logic to skip the tests based on Tests class and configured Microversion
range.
api_version_utils.check_skip_with_microversion function can be used
to automatically skip the tests which do not fall under configured
Microversion range.
For example:

.. code-block:: python

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
For example:

.. code-block:: python

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
For example:

.. code-block:: python

      COMPUTE_MICROVERSION = None

      class BaseClient1(rest_client.RestClient):
          api_microversion_header_name = 'X-OpenStack-Nova-API-Version'

Now test class can set the selected Microversion on required service clients
using fixture which can take care of resetting the same once tests is completed.
For example:

.. code-block:: python

    def setUp(self):
        super(BaseTestCase1, self).setUp()
        self.useFixture(api_microversion_fixture.APIMicroversionFixture(
            self.request_microversion))

Service clients needs to add set Microversion in API request header which
can be done by overriding the get_headers() method of rest_client.
For example:

.. code-block:: python

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

.. note:: Microversion testing is supported at test class level not at
      individual test case level.

For example:

Below test is applicable for Microversion from 2.2 till 2.9:

.. code-block:: python

    class BaseTestCase1(api_version_utils.BaseMicroversionTest,
                        tempest.test.BaseTestCase):

        [..]


    class Test1(BaseTestCase1):
        min_microversion = '2.2'
        max_microversion = '2.9'

        [..]

Below test is applicable for Microversion from 2.10 till latest:

.. code-block:: python

    class Test2(BaseTestCase1):
        min_microversion = '2.10'
        max_microversion = 'latest'

        [..]


Notes about Compute Microversion Tests
""""""""""""""""""""""""""""""""""""""

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

  .. _2.1:  https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id1

  * `2.2`_

  .. _2.2: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id2

  * `2.6`_

  .. _2.6: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id5

  * `2.10`_

  .. _2.10: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id9

  * `2.20`_

  .. _2.20: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id18

  * `2.21`_

  .. _2.21: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id19

  * `2.25`_

  .. _2.25: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#maximum-in-mitaka

  * `2.32`_

  .. _2.32: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id29

  * `2.37`_

  .. _2.37: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id34

  * `2.42`_

  .. _2.42: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#maximum-in-ocata

  * `2.47`_

  .. _2.47: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id42

  * `2.48`_

  .. _2.48: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id43

  * `2.60`_

  .. _2.60: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html#id54

* Volume

  * `3.3`_

  .. _3.3:  https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html#id3

  * `3.9`_

  .. _3.9:  https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html#id9

  * `3.11`_

  .. _3.11:  https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html#id11

  * `3.12`_

  .. _3.12:  https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html#id12

  * `3.13`_

  .. _3.13:  https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html#id13

  * `3.14`_

  .. _3.14:  https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html#id14

  * `3.19`_

  .. _3.19:  https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html#id18

  * `3.20`_

  .. _3.20:  https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html#id19
