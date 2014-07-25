.. _stress_field_guide:

Tempest Field Guide to Stress Tests
===================================

OpenStack is a distributed, asynchronous system that is prone to race condition
bugs. These bugs will not be easily found during
functional testing but will be encountered by users in large deployments in a
way that is hard to debug. The stress test tries to cause these bugs to happen
in a more controlled environment.


Environment
-----------
This particular framework assumes your working Nova cluster understands Nova
API 2.0. The stress tests can read the logs from the cluster. To enable this
you have to provide the hostname to call 'nova-manage' and
the private key and user name for ssh to the cluster in the
[stress] section of tempest.conf. You also need to provide the
location of the log files:

	target_logfiles = "regexp to all log files to be checked for errors"
	target_private_key_path = "private ssh key for controller and log file nodes"
	target_ssh_user = "username for controller and log file nodes"
	target_controller = "hostname or ip of controller node (for nova-manage)
	log_check_interval = "time between checking logs for errors (default 60s)"

To activate logging on your console please make sure that you activate `use_stderr`
in tempest.conf or use the default `logging.conf.sample` file.

Running default stress test set
-------------------------------

The stress test framework can automatically discover test inside the tempest
test suite. All test flag with the `@stresstest` decorator will be executed.
In order to use this discovery you have to be in the tempest root directory
and execute the following:

	run-tempest-stress -a -d 30

Running the sample test
-----------------------

To test installation, do the following:

	run-tempest-stress -t tempest/stress/etc/server-create-destroy-test.json -d 30

This sample test tries to create a few VMs and kill a few VMs.


Additional Tools
----------------

Sometimes the tests don't finish, or there are failures. In these
cases, you may want to clean out the nova cluster. We have provided
some scripts to do this in the ``tools`` subdirectory.
You can use the following script to destroy any keypairs,
floating ips, and servers:

tempest/stress/tools/cleanup.py
