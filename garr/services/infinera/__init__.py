# Copyright 2025 GARR.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
TNMS (Transport Network Management System) API Client Package.

This package provides a client interface for interacting with the TNMS API.
It handles authentication and provides methods for device management operations.

Example:
    >>> from services.infinera import tnms_client
    >>> response = tnms_client.flexils(device_uuid, device_name).enter_osnc(**kwargs)
    >>> devices = tnms_client.data.equipment.devices.retrieve(fields=["name", "type"])

Note:
    The package is configured using environment variables.
    # removed auth info for sharing on public repo

    The client instance is created as a singleton from the environment variables.

    The methods of tnms_client.data and tnms_client.flexils(device_uuid, device_name)
    are create dynamically and thus there is no type hinting for them.
    See retrieve method for data.
    See the flexils.commands.command_name module for flexils methods.
"""

import logging
from typing import Final

from .core.client import TnmsClient  # noqa: TID252
from .core.exceptions import (  # noqa: TID252
    ApiError,
    AuthenticationError,
    TnmsClientError,
    ValidationError,
)
from .flexils.exceptions import FlexILSClientError, TL1CommandDeniedError  # noqa: TID252
from .g30.client import G30Client  # noqa: TID252
from .g42.client import G42Client  # noqa: TID252

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


__version__: Final[str] = "1.0.0"

g30_client = G30Client
g42_client = G42Client
# Singleton instance configured from environment variables
# with automatic re-authentication
tnms_client: Final[TnmsClient] = TnmsClient.from_env()
__all__ = [
    "ApiError",
    "AuthenticationError",
    "FlexILSClientError",
    "TL1CommandDeniedError",
    "TnmsClientError",
    "ValidationError",
    "__version__",
    "g30_client",
    "g42_client",
    "tnms_client",
]
