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

"""TNMS API client implementation."""

import logging
import os
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import requests
from requests.exceptions import HTTPError

from ..flexils.client import FlexILSClient
from .endpoints import Data, Operations
from .exceptions import ApiError, AuthenticationError, ValidationError

T = TypeVar("T")

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def requires_auth(func: Callable) -> Callable:
    """Decorator to ensure valid authentication before making requests."""

    @wraps(func)
    def wrapper(self: "TnmsClient", *args, **kwargs):
        # removed auth info for sharing on public repo
        raise NotImplementedError



class TnmsClient:
    """TNMS API client with automatic authentication handling."""

    def __init__(
        self, # removed auth info for sharing on public repo
    ):
        # removed auth info for sharing on public repo
        self.data = Data(self)
        self.operations = Operations(self)

    @classmethod
    def from_env(cls) -> "TnmsClient":
        """Create client instance from environment variables."""
        # removed auth info for sharing on public repo
        raise NotImplementedError

    def _authenticate(self) -> None:
        """Get and store authentication token."""
        # removed auth info for sharing on public repo
        raise NotImplementedError

    @requires_auth
    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        """Make authenticated API request."""
        url = self.url + path
        log.debug(f"{method} {url} {kwargs}")
        response = self._session.request(method, url, **kwargs)
        response.raise_for_status()
        log.debug(f"Response: {response.text}")
        return response.json() if method != "DELETE" else {}

    def flexils(self, device_uuid: str, device_tid: str) -> "FlexILSClient":
        """Create a FlexILS client for a specific device."""
        return FlexILSClient(self, device_uuid, device_tid)
