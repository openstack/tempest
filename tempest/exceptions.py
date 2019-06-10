# Copyright 2012 OpenStack Foundation
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


from tempest.lib import exceptions


class BuildErrorException(exceptions.TempestException):
    message = "Server %(server_id)s failed to build and is in ERROR status"


class SnapshotNotFoundException(exceptions.TempestException):
    message = "Server snapshot image %(image_id)s not found."


class ImageKilledException(exceptions.TempestException):
    message = "Image %(image_id)s 'killed' while waiting for '%(status)s'"


class AddImageException(exceptions.TempestException):
    message = "Image %(image_id)s failed to become ACTIVE in the allotted time"


class VolumeResourceBuildErrorException(exceptions.TempestException):
    message = ("%(resource_name)s %(resource_id)s failed to build and is in "
               "ERROR status")


class VolumeRestoreErrorException(exceptions.TempestException):
    message = "Volume %(volume_id)s failed to restore and is in ERROR status"


class VolumeExtendErrorException(exceptions.TempestException):
    message = ("Volume %(volume_id)s failed to extend and "
               "is in error_extending status")


class StackBuildErrorException(exceptions.TempestException):
    message = ("Stack %(stack_identifier)s is in %(stack_status)s status "
               "due to '%(stack_status_reason)s'")


class ServerUnreachable(exceptions.TempestException):
    message = ("Server %(server_id)s is not reachable via "
               "the configured network")


class InvalidServiceTag(exceptions.TempestException):
    message = "Invalid service tag"
