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

import base64
import logging
import os
from typing import Any

import requests

from .data import Data
from .operations import Operations

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# removed auth info for sharing on public repo

class G42Client:
    """G42 API client with automatic authentication handling."""

    def __init__(self, lo_ip: str | None = None, mngmt_ip: str | None = None):
        self.url = None
        self.fallback_url = None

        if mngmt_ip:
            self.url = f"https://{mngmt_ip}:8181/restconf"
        if lo_ip:
            self.fallback_url = self.url
            self.url = f"https://{lo_ip}:8181/restconf"
        if not self.url:
            msg = "Either lo_ip or mngmt_ip must be provided"
            raise ValueError(msg)

        self._session = requests.Session()
        self._session.verify = False
        self._session.headers.update(
            {
                "Content-Type": "application/yang-data+json",
                # removed auth info for sharing on public repo
            }
        )
        self.data = Data(self)
        self.operations = Operations(self)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        """Make authenticated API request."""

        def _helper(base_url: str):
            url = base_url + path
            log.debug(f"{method} {url} {kwargs}")
            response = self._session.request(method, url, **kwargs)
            log.debug(f"Response: {response.text}")
            response.raise_for_status()
            return response.json() if response.text else {}

        try:
            result = _helper(self.url)
        except requests.RequestException as e:
            if not self.fallback_url:
                raise e
            result = _helper(self.fallback_url)
        return result
