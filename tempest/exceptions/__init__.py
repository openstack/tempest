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

from tempest.exceptions import base


class InvalidConfiguration(base.TempestException):
    message = "Invalid Configuration"


class InvalidHttpSuccessCode(base.RestClientException):
    message = "The success code is different than the expected one"


class NotFound(base.RestClientException):
    message = "Object not found"


class Unauthorized(base.RestClientException):
    message = 'Unauthorized'


class InvalidServiceTag(base.RestClientException):
    message = "Invalid service tag"


class TimeoutException(base.TempestException):
    message = "Request timed out"


class BuildErrorException(base.TempestException):
    message = "Server %(server_id)s failed to build and is in ERROR status"


class ImageKilledException(base.TempestException):
    message = "Image %(image_id)s 'killed' while waiting for '%(status)s'"


class AddImageException(base.TempestException):
    message = "Image %(image_id)s failed to become ACTIVE in the allotted time"


class EC2RegisterImageException(base.TempestException):
    message = ("Image %(image_id)s failed to become 'available' "
               "in the allotted time")


class VolumeBuildErrorException(base.TempestException):
    message = "Volume %(volume_id)s failed to build and is in ERROR status"


class SnapshotBuildErrorException(base.TempestException):
    message = "Snapshot %(snapshot_id)s failed to build and is in ERROR status"


class VolumeBackupException(base.TempestException):
    message = "Volume backup %(backup_id)s failed and is in ERROR status"


class StackBuildErrorException(base.TempestException):
    message = ("Stack %(stack_identifier)s is in %(stack_status)s status "
               "due to '%(stack_status_reason)s'")


class BadRequest(base.RestClientException):
    message = "Bad request"


class UnprocessableEntity(base.RestClientException):
    message = "Unprocessable entity"


class AuthenticationFailure(base.RestClientException):
    message = ("Authentication with user %(user)s and password "
               "%(password)s failed auth using tenant %(tenant)s.")


class EndpointNotFound(base.TempestException):
    message = "Endpoint not found"


class RateLimitExceeded(base.TempestException):
    message = "Rate limit exceeded"


class OverLimit(base.TempestException):
    message = "Quota exceeded"


class ServerFault(base.TempestException):
    message = "Got server fault"


class ImageFault(base.TempestException):
    message = "Got image fault"


class IdentityError(base.TempestException):
    message = "Got identity error"


class Conflict(base.RestClientException):
    message = "An object with that identifier already exists"


class SSHTimeout(base.TempestException):
    message = ("Connection to the %(host)s via SSH timed out.\n"
               "User: %(user)s, Password: %(password)s")


class SSHExecCommandFailed(base.TempestException):
    """Raised when remotely executed command returns nonzero status."""
    message = ("Command '%(command)s', exit status: %(exit_status)d, "
               "Error:\n%(strerror)s")


class ServerUnreachable(base.TempestException):
    message = "The server is not reachable via the configured network"


class TearDownException(base.TempestException):
    message = "%(num)d cleanUp operation failed"


class ResponseWithNonEmptyBody(base.RFCViolation):
    message = ("RFC Violation! Response with %(status)d HTTP Status Code "
               "MUST NOT have a body")


class ResponseWithEntity(base.RFCViolation):
    message = ("RFC Violation! Response with 205 HTTP Status Code "
               "MUST NOT have an entity")


class InvalidHTTPResponseBody(base.RestClientException):
    message = "HTTP response body is invalid json or xml"


class InvalidContentType(base.RestClientException):
    message = "Invalid content type provided"


class UnexpectedResponseCode(base.RestClientException):
    message = "Unexpected response code received"
