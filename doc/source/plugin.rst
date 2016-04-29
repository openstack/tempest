=============================
Tempest Test Plugin Interface
=============================

Tempest has an external test plugin interface which enables anyone to integrate
an external test suite as part of a tempest run. This will let any project
leverage being run with the rest of the tempest suite while not requiring the
tests live in the tempest tree.

Creating a plugin
=================

Creating a plugin is fairly straightforward and doesn't require much additional
effort on top of creating a test suite using tempest.lib. One thing to note with
doing this is that the interfaces exposed by tempest are not considered stable
(with the exception of configuration variables which ever effort goes into
ensuring backwards compatibility). You should not need to import anything from
tempest itself except where explicitly noted. If there is an interface from
tempest that you need to rely on in your plugin it likely needs to be migrated
to tempest.lib. In that situation, file a bug, push a migration patch, etc. to
expedite providing the interface in a reliable manner.

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
project to enable tempest to find the plugin. The entry point must be added
to the "tempest.test_plugins" namespace.

If you are using pbr this is fairly straightforward, in the setup.cfg just add
something like the following::

  [entry_points]
  tempest.test_plugins =
      plugin_name = module.path:PluginClass

Standalone Plugin vs In-repo Plugin
-----------------------------------

Since all that's required for a plugin to be detected by tempest is a valid
setuptools entry point in the proper namespace there is no difference from the
tempest perspective on either creating a separate python package to
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
install the right version of a project in the same python namespace as tempest
they simply need to pip install the plugin in that namespace. It also means
that users don't have to worry about inadvertently installing a tempest plugin
when they install another package.

.. _Branchless Tempest Spec: http://specs.openstack.org/openstack/qa-specs/specs/tempest/implemented/branchless-tempest.html

The sole advantage to integrating a plugin into an existing python project is
that it enables you to land code changes at the same time you land test changes
in the plugin. This reduces some of the burden on contributors by not having
to land 2 changes to add a new API feature and then test it and doing it as a
single combined commit.


Plugin Class
============

To provide tempest with all the required information it needs to be able to run
your plugin you need to create a plugin class which tempest will load and call
to get information when it needs. To simplify creating this tempest provides an
abstract class that should be used as the parent for your plugin. To use this
you would do something like the following::

  from tempest.test_discover import plugins

  class MyPlugin(plugins.TempestPlugin):

Then you need to ensure you locally define all of the methods in the abstract
class, you can refer to the api doc below for a reference of what that entails.

Abstract Plugin Class
---------------------

.. autoclass:: tempest.test_discover.plugins.TempestPlugin
   :members:

Plugin Structure
================
While there are no hard and fast rules for the structure a plugin, there are
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

That will mirror what people expect from tempest. The file

* **config.py**: contains any plugin specific configuration variables
* **plugin.py**: contains the plugin class used for the entry point
* **tests**: the directory where test discovery will be run, all tests should
             be under this dir
* **services**: where the plugin specific service clients are

Additionally, when you're creating the plugin you likely want to follow all
of the tempest developer and reviewer documentation to ensure that the tests
being added in the plugin act and behave like the rest of tempest.

Dealing with configuration options
----------------------------------

Historically Tempest didn't provide external guarantees on its configuration
options. However, with the introduction of the plugin interface this is no
longer the case. An external plugin can rely on using any configuration option
coming from Tempest, there will be at least a full deprecation cycle for any
option before it's removed. However, just the options provided by Tempest
may not be sufficient for the plugin. If you need to add any plugin specific
configuration options you should use the ``register_opts`` and
``get_opt_lists`` methods to pass them to Tempest when the plugin is loaded.
When adding configuration options the ``register_opts`` method gets passed the
CONF object from tempest. This enables the plugin to add options to both
existing sections and also create new configuration sections for new options.

Using Plugins
=============

Tempest will automatically discover any installed plugins when it is run. So by
just installing the python packages which contain your plugin you'll be using
them with tempest, nothing else is really required.

However, you should take care when installing plugins. By their very nature
there are no guarantees when running tempest with plugins enabled about the
quality of the plugin. Additionally, while there is no limitation on running
with multiple plugins it's worth noting that poorly written plugins might not
properly isolate their tests which could cause unexpected cross interactions
between plugins.

Notes for using plugins with virtualenvs
----------------------------------------

When using a tempest inside a virtualenv (like when running under tox) you have
to ensure that the package that contains your plugin is either installed in the
venv too or that you have system site-packages enabled. The virtualenv will
isolate the tempest install from the rest of your system so just installing the
plugin package on your system and then running tempest inside a venv will not
work.

Tempest also exposes a tox job, all-plugin, which will setup a tox virtualenv
with system site-packages enabled. This will let you leverage tox without
requiring to manually install plugins in the tox venv before running tests.
