.. _tempest_plugin:

=============================
Tempest Test Plugin Interface
=============================

Tempest has an external test plugin interface which enables anyone to integrate
an external test suite as part of a Tempest run. This will let any project
leverage being run with the rest of the Tempest suite while not requiring the
tests live in the Tempest tree.

Creating a plugin
=================

Creating a plugin is fairly straightforward and doesn't require much additional
effort on top of creating a test suite using tempest.lib. One thing to note with
doing this is that the interfaces exposed by Tempest are not considered stable
(with the exception of configuration variables whichever effort goes into
ensuring backward compatibility). You should not need to import anything from
Tempest itself except where explicitly noted.

Stable Tempest APIs plugins may use
-----------------------------------

As noted above, several Tempest APIs are acceptable to use from plugins, while
others are not. A list of stable APIs available to plugins is provided below:

* tempest.lib.*
* tempest.config
* tempest.test_discover.plugins
* tempest.common.credentials_factory
* tempest.clients
* tempest.test

If there is an interface from Tempest that you need to rely on in your plugin
which is not listed above, it likely needs to be migrated to tempest.lib. In
that situation, file a bug, push a migration patch, etc. to expedite providing
the interface in a reliable manner.

Plugin Cookiecutter
-------------------

In order to create the basic structure with base classes and test directories
you can use the tempest-plugin-cookiecutter project::

  > pip install -U cookiecutter && cookiecutter https://git.openstack.org/openstack/tempest-plugin-cookiecutter

  Cloning into 'tempest-plugin-cookiecutter'...
  remote: Counting objects: 17, done.
  remote: Compressing objects: 100% (13/13), done.
  remote: Total 17 (delta 1), reused 14 (delta 1)
  Unpacking objects: 100% (17/17), done.
  Checking connectivity... done.
  project (default is "sample")? foo
  testclass (default is "SampleTempestPlugin")? FooTempestPlugin

This would create a folder called ``foo_tempest_plugin/`` with all necessary
basic classes. You only need to move/create your test in
``foo_tempest_plugin/tests``.

Entry Point
-----------

Once you've created your plugin class you need to add an entry point to your
project to enable Tempest to find the plugin. The entry point must be added
to the "tempest.test_plugins" namespace.

If you are using pbr this is fairly straightforward, in the setup.cfg just add
something like the following:

.. code-block:: ini

  [entry_points]
  tempest.test_plugins =
      plugin_name = module.path:PluginClass

Standalone Plugin vs In-repo Plugin
-----------------------------------

Since all that's required for a plugin to be detected by Tempest is a valid
setuptools entry point in the proper namespace there is no difference from the
Tempest perspective on either creating a separate python package to
house the plugin or adding the code to an existing python project. However,
there are tradeoffs to consider when deciding which approach to take when
creating a new plugin.

If you create a separate python project for your plugin this makes a lot of
things much easier. Firstly it makes packaging and versioning much simpler, you
can easily decouple the requirements for the plugin from the requirements for
the other project. It lets you version the plugin independently and maintain a
single version of the test code across project release boundaries (see the
`Branchless Tempest Spec`_ for more details on this). It also greatly
simplifies the install time story for external users. Instead of having to
install the right version of a project in the same python namespace as Tempest
they simply need to pip install the plugin in that namespace. It also means
that users don't have to worry about inadvertently installing a Tempest plugin
when they install another package.

.. _Branchless Tempest Spec: http://specs.openstack.org/openstack/qa-specs/specs/tempest/implemented/branchless-tempest.html

The sole advantage to integrating a plugin into an existing python project is
that it enables you to land code changes at the same time you land test changes
in the plugin. This reduces some of the burden on contributors by not having
to land 2 changes to add a new API feature and then test it and doing it as a
single combined commit.


Plugin Class
============

To provide Tempest with all the required information it needs to be able to run
your plugin you need to create a plugin class which Tempest will load and call
to get information when it needs. To simplify creating this Tempest provides an
abstract class that should be used as the parent for your plugin. To use this
you would do something like the following:

.. code-block:: python

  from tempest.test_discover import plugins

  class MyPlugin(plugins.TempestPlugin):

Then you need to ensure you locally define all of the mandatory methods in the
abstract class, you can refer to the api doc below for a reference of what that
entails.

Abstract Plugin Class
---------------------

.. autoclass:: tempest.test_discover.plugins.TempestPlugin
   :members:

Plugin Structure
================
While there are no hard and fast rules for the structure of a plugin, there are
basically no constraints on what the plugin looks like as long as the 2 steps
above are done. However,  there are some recommended patterns to follow to make
it easy for people to contribute and work with your plugin. For example, if you
create a directory structure with something like::

    plugin_dir/
      config.py
      plugin.py
      tests/
        api/
        scenario/
      services/
        client.py

That will mirror what people expect from Tempest. The file

* **config.py**: contains any plugin specific configuration variables
* **plugin.py**: contains the plugin class used for the entry point
* **tests**: the directory where test discovery will be run, all tests should
             be under this dir
* **services**: where the plugin specific service clients are

Additionally, when you're creating the plugin you likely want to follow all
of the Tempest developer and reviewer documentation to ensure that the tests
being added in the plugin act and behave like the rest of Tempest.

Dealing with configuration options
----------------------------------

Historically, Tempest didn't provide external guarantees on its configuration
options. However, with the introduction of the plugin interface, this is no
longer the case. An external plugin can rely on using any configuration option
coming from Tempest, there will be at least a full deprecation cycle for any
option before it's removed. However, just the options provided by Tempest
may not be sufficient for the plugin. If you need to add any plugin specific
configuration options you should use the ``register_opts`` and
``get_opt_lists`` methods to pass them to Tempest when the plugin is loaded.
When adding configuration options the ``register_opts`` method gets passed the
CONF object from Tempest. This enables the plugin to add options to both
existing sections and also create new configuration sections for new options.

Service Clients
---------------

If a plugin defines a service client, it is beneficial for it to implement the
``get_service_clients`` method in the plugin class. All service clients which
are exposed via this interface will be automatically configured and be
available in any instance of the service clients class, defined in
``tempest.lib.services.clients.ServiceClients``. In case multiple plugins are
installed, all service clients from all plugins will be registered, making it
easy to write tests which rely on multiple APIs whose service clients are in
different plugins.

Example implementation of ``get_service_clients``:

.. code-block:: python

    def get_service_clients(self):
        # Example implementation with two service clients
        my_service1_config = config.service_client_config('my_service')
        params_my_service1 = {
            'name': 'my_service_v1',
            'service_version': 'my_service.v1',
            'module_path': 'plugin_tempest_tests.services.my_service.v1',
            'client_names': ['API1Client', 'API2Client'],
        }
        params_my_service1.update(my_service_config)
        my_service2_config = config.service_client_config('my_service')
        params_my_service2 = {
            'name': 'my_service_v2',
            'service_version': 'my_service.v2',
            'module_path': 'plugin_tempest_tests.services.my_service.v2',
            'client_names': ['API1Client', 'API2Client'],
        }
        params_my_service2.update(my_service2_config)
        return [params_my_service1, params_my_service2]

Parameters:

* **name**: Name of the attribute used to access the ``ClientsFactory`` from
  the ``ServiceClients`` instance. See example below.
* **service_version**: Tempest enforces a single implementation for each
  service client. Available service clients are held in a ``ClientsRegistry``
  singleton, and registered with ``service_version``, which means that
  ``service_version`` must be unique and it should represent the service API
  and version implemented by the service client.
* **module_path**: Relative to the service client module, from the root of the
  plugin.
* **client_names**: Name of the classes that implement service clients in the
  service clients module.

Example usage of the service clients in tests:

.. code-block:: python

   # my_creds is instance of tempest.lib.auth.Credentials
   # identity_uri is v2 or v3 depending on the configuration
   from tempest.lib.services import clients

   my_clients = clients.ServiceClients(my_creds, identity_uri)
   my_service1_api1_client = my_clients.my_service_v1.API1Client()
   my_service2_api1_client = my_clients.my_service_v2.API1Client(my_args='any')

Automatic configuration and registration of service clients imposes some extra
constraints on the structure of the configuration options exposed by the
plugin.

First ``service_version`` should be in the format `service_config[.version]`.
The `.version` part is optional, and should only be used if there are multiple
versions of the same API available. The `service_config` must match the name of
a configuration options group defined by the plugin. Different versions of one
API must share the same configuration group.

Second the configuration options group `service_config` must contain the
following options:

* `catalog_type`: corresponds to `service` in the catalog
* `endpoint_type`

The following options will be honoured if defined, but they are not mandatory,
as they do not necessarily apply to all service clients.

* `region`: default to identity.region
* `build_timeout` : default to compute.build_timeout
* `build_interval`: default to compute.build_interval

Third the service client classes should inherit from ``RestClient``, should
accept generic keyword arguments, and should pass those arguments to the
``__init__`` method of ``RestClient``. Extra arguments can be added. For
instance:

.. code-block:: python

   class MyAPIClient(rest_client.RestClient):

    def __init__(self, auth_provider, service, region,
                 my_arg, my_arg2=True, **kwargs):
        super(MyAPIClient, self).__init__(
            auth_provider, service, region, **kwargs)
        self.my_arg = my_arg
        self.my_args2 = my_arg

Finally the service client should be structured in a python module, so that all
service client classes are importable from it. Each major API version should
have its own module.

The following folder and module structure is recommended for a single major
API version::

    plugin_dir/
      services/
        __init__.py
        client_api_1.py
        client_api_2.py

The content of __init__.py module should be:

.. code-block:: python

   from client_api_1.py import API1Client
   from client_api_2.py import API2Client

   __all__ = ['API1Client', 'API2Client']

The following folder and module structure is recommended for multiple major
API version::

    plugin_dir/
      services/
        v1/
           __init__.py
           client_api_1.py
           client_api_2.py
        v2/
           __init__.py
           client_api_1.py
           client_api_2.py

The content each of __init__.py module under vN should be:

.. code-block:: python

   from client_api_1.py import API1Client
   from client_api_2.py import API2Client

   __all__ = ['API1Client', 'API2Client']

Using Plugins
=============

Tempest will automatically discover any installed plugins when it is run. So by
just installing the python packages which contain your plugin you'll be using
them with Tempest, nothing else is really required.

However, you should take care when installing plugins. By their very nature
there are no guarantees when running Tempest with plugins enabled about the
quality of the plugin. Additionally, while there is no limitation on running
with multiple plugins, it's worth noting that poorly written plugins might not
properly isolate their tests which could cause unexpected cross interactions
between plugins.

Notes for using plugins with virtualenvs
----------------------------------------

When using a Tempest inside a virtualenv (like when running under tox) you have
to ensure that the package that contains your plugin is either installed in the
venv too or that you have system site-packages enabled. The virtualenv will
isolate the Tempest install from the rest of your system so just installing the
plugin package on your system and then running Tempest inside a venv will not
work.

Tempest also exposes a tox job, all-plugin, which will setup a tox virtualenv
with system site-packages enabled. This will let you leverage tox without
requiring to manually install plugins in the tox venv before running tests.
