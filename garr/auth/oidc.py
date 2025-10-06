"""Module contains the OIDC Authentication class."""

import re
from collections.abc import Callable
from functools import wraps
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any

from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from httpx import AsyncClient
from oauth2_lib.fastapi import OIDCAuth, OIDCUserModel
from oauth2_lib.settings import oauth2lib_settings
from structlog import get_logger

logger = get_logger(__name__)

_CALLBACK_STEP_API_URL_PATTERN = re.compile(
    r"^/api/processes/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
    r"/callback/([0-9a-zA-Z\-_]+)$"
)


def _is_client_credentials_token(intercepted_token: dict) -> bool:
    return "sub" not in intercepted_token


def _is_callback_step_endpoint(request: Request) -> bool:
    """Check if the request is a callback step API call."""
    return re.match(_CALLBACK_STEP_API_URL_PATTERN, request.url.path) is not None


def ensure_openid_config_loaded(func: Callable) -> Callable:
    """Ensure that the openid_config is loaded before calling the function."""

    @wraps(func)
    async def wrapper(self: OIDCAuth, async_request: AsyncClient, *args: Any, **kwargs: Any) -> dict:
        await self.check_openid_config(async_request)
        return await func(self, async_request, *args, **kwargs)

    return wrapper


def validate_env_vars(env_vars: dict[str, str]) -> None:
    missing = [name for name, value in env_vars.items() if not value]
    if missing:
        raise ValueError(f"Missing required env var: {', '.join(missing)}")  # noqa: EM102


class CustomOIDCAuth(OIDCAuth):
    """OIDCAuth e' una classe placeholder per definire il layer di authn e costruita su OAuth,
    che per definizione si occupa di recuperare l'access_token da un authz server.

    Codice ereditato dall'implementazione di Geant: https://u.garr.it/9oC65

    Nell'implementazione, la classe valida le credenziali con l'AAI proxy via UserInfo endpoint.
    """

    def __init__(self):
        """Verifica l'assegnazioni delle variabili e chiama il parent constructor."""
        # Early fail.
        # Senza un controllo, il default e' di restituire un 401 unauthorized al momento di introspection
        # oauth2lib_settings usa pydantic come validatore ma e' inizializzato come stringa vuota e perde di utilita'
        validate_env_vars(
            {
                "OIDC_BASE_URL": oauth2lib_settings.OIDC_BASE_URL,
                "OIDC_CONF_URL": oauth2lib_settings.OIDC_CONF_URL,
                "OAUTH2_RESOURCE_SERVER_ID": oauth2lib_settings.OAUTH2_RESOURCE_SERVER_ID,
                "OAUTH2_RESOURCE_SERVER_SECRET": oauth2lib_settings.OAUTH2_RESOURCE_SERVER_SECRET,
            }
        )

        logger.info(f"Initializing OIDC with base URL: {oauth2lib_settings.OIDC_BASE_URL}")  # noqa: G004
        logger.info(f"Resource client ID: {oauth2lib_settings.OAUTH2_RESOURCE_SERVER_ID}")  # noqa: G004

        super().__init__(
            openid_url=oauth2lib_settings.OIDC_BASE_URL,
            openid_config_url=oauth2lib_settings.OIDC_CONF_URL,
            resource_server_id=oauth2lib_settings.OAUTH2_RESOURCE_SERVER_ID,
            resource_server_secret=oauth2lib_settings.OAUTH2_RESOURCE_SERVER_SECRET,
            oidc_user_model_cls=OIDCUserModel,
        )

    @staticmethod
    async def is_bypassable_request(request: Request) -> bool:
        """Check if the request is a callback step API call."""
        return _is_callback_step_endpoint(request=request)

    @ensure_openid_config_loaded
    async def userinfo(self, async_request: AsyncClient, token: str) -> OIDCUserModel:
        """Recupera userinfo dal server OpenID.

        Args:
            async_request: The async request.
            token: The access token.

        Returns:
            OIDCUserModel: OIDC user model from openid server.
        """
        assert self.openid_config is not None, "OpenID config is not loaded"  # noqa: S101

        # verifico innanzitutto che il token sia valido e in caso blocco
        intercepted_token = await self.introspect_token(async_request, token)
        client_id = intercepted_token.get("client_id")
        # Controllo dell'attributo 'sub':
        # - Authorization Code / Implicit Flow (utente loggato) > attributo presente.
        # - Client Credentials Flow (machine-to-machine) > attributo assente.
        if _is_client_credentials_token(intercepted_token):
            return OIDCUserModel(client_id=client_id)

        response = await async_request.post(
            self.openid_config.userinfo_endpoint,
            data={"token": token},
            headers={"Authorization": f"Bearer {token}"},
        )
        try:
            user_info = dict(response.json())
        except JSONDecodeError as err:
            logger.debug(
                "Unable to parse userinfo response",
                detail=response.text,
                resource_server_id=self.resource_server_id,
                openid_url=self.openid_url,
            )
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=response.text) from err
        logger.debug("Response from openid userinfo", response=user_info)

        if response.status_code not in range(200, 300):
            logger.debug(
                "Userinfo cannot find an active token, user unauthorized",
                detail=response.text,
                resource_server_id=self.resource_server_id,
                openid_url=self.openid_url,
            )
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=response.text)

        user_info["client_id"] = client_id

        return OIDCUserModel(user_info)

    @ensure_openid_config_loaded
    async def introspect_token(self, async_request: AsyncClient, token: str) -> dict:
        """Introspezione dell'access token per verificarne la validita'.

        Args:
            async_request: The async request
            token: the access_token

        Returns:
            dict from openid server
        """
        assert self.openid_config is not None, "OpenID config is not loaded"  # noqa: S101

        endpoint = self.openid_config.introspect_endpoint or self.openid_config.introspection_endpoint or ""
        response = await async_request.post(
            endpoint,
            data={
                "token": token,
                "client_id": self.resource_server_id,
                "client_secret": self.resource_server_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        try:
            oidc_response = dict(response.json())
        except JSONDecodeError as err:
            logger.debug(
                "Unable to parse introspect response",
                detail=response.text,
                resource_server_id=self.resource_server_id,
                openid_url=self.openid_url,
            )
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=response.text) from err

        logger.debug("Response from openid introspect", response=oidc_response)

        if response.status_code not in range(200, 300):
            logger.debug(
                "Introspect cannot find an active token, user unauthorized",
                detail=response.text,
                resource_server_id=self.resource_server_id,
                openid_url=self.openid_url,
            )
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=response.text)

        if "active" not in oidc_response:
            # unico attributo per verificare lo stato di validita' del token
            logger.error("Token does not have the mandatory 'active' key, probably caused by a caching problem")
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Missing active key")
        if not oidc_response.get("active"):
            logger.info("User is not active", user_info=oidc_response)
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="User is not active")

        return oidc_response
