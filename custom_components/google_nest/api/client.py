"""Nest API Client."""
from __future__ import annotations

from aiohttp import ClientSession, ClientTimeout, ContentTypeError, FormData
from http import HTTPStatus
import json
import logging
import os
from random import randint
import time
from types import TracebackType
from typing import Any

from .const import (
    APP_LAUNCH_URL_FORMAT,
    DEFAULT_NEST_ENVIRONMENT,
    NEST_AUTH_URL_JWT,
    NEST_REQUEST,
    SAVE_RESPONSE_LOCATION,
    TOKEN_URL,
    USER_AGENT,
)
from .exceptions import (
    BadCredentialsException,
    BadGatewayException,
    GatewayTimeoutException,
    NotAuthenticatedException,
    NestException,
)
from .models import (
    GoogleAuthResponse,
    GoogleAuthResponseForCookies,
    NestAuthResponse,
    NestEnvironment,
    NestResponse,
)

_LOGGER = logging.getLogger(__package__)


class NestClient:
    """Interface class for the Nest API."""

    auth: GoogleAuthResponseForCookies | None = None
    environment: NestEnvironment
    nest_session: NestResponse | None = None
    session: ClientSession
    transport_url: str | None = None

    def __init__(
        self,
        session: ClientSession | None = None,
        refresh_token: str | None = None,
        issue_token: str | None = None,
        cookies: str | None = None,
        environment: NestEnvironment = DEFAULT_NEST_ENVIRONMENT,
        save_response_enabled: bool = False,
    ) -> None:
        """Initialize NestClient."""

        self.session = session if session else ClientSession()
        self.refresh_token = refresh_token
        self.issue_token = issue_token
        self.cookies = cookies
        self.environment = environment
        self.save_response_enabled = save_response_enabled

    async def __aenter__(self) -> NestClient:
        """__aenter__."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """__aexit__."""
        await self.session.close()

    async def get_access_token(self) -> GoogleAuthResponse:
        """Get a Nest access token."""

        if self.refresh_token:
            await self.get_access_token_from_refresh_token(self.refresh_token)
        elif self.issue_token and self.cookies:
            await self.get_access_token_from_cookies(self.issue_token, self.cookies)
        else:
            raise Exception("No credentials")
        _LOGGER.debug(f"Got access token: {self.nest_session.access_token}")

        return self.auth

    async def get_access_token_from_refresh_token(
        self, refresh_token: str | None = None
    ) -> GoogleAuthResponse:
        """Get a Nest refresh token from an authorization code."""

        if refresh_token:
            self.refresh_token = refresh_token

        if not self.refresh_token:
            raise Exception("No refresh token")

        async with self.session.post(
            TOKEN_URL,
            data=FormData(
                {
                    "refresh_token": self.refresh_token,
                    "client_id": self.environment.client_id,
                    "grant_type": "refresh_token",
                }
            ),
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        ) as response:
            result = await response.json()
            self.save_response(response=result, name="refresh_token")

            if "error" in result:
                if result["error"] == "invalid_grant":
                    raise BadCredentialsException(result["error"])

                raise Exception(result["error"])

            self.auth = GoogleAuthResponse(**result)

            return self.auth

    async def get_access_token_from_cookies(
        self, issue_token: str | None = None, cookies: str | None = None
    ) -> GoogleAuthResponse:
        """Get a Nest refresh token from an issue token and cookies."""

        if issue_token:
            self.issue_token = issue_token

        if cookies:
            self.cookies = cookies

        if not self.issue_token:
            raise Exception("No issue token")

        if not self.cookies:
            raise Exception("No cookies")

        async with self.session.get(
            issue_token,
            headers={
                "Sec-Fetch-Mode": "cors",
                "User-Agent": USER_AGENT,
                "X-Requested-With": "XmlHttpRequest",
                "Referer": "https://accounts.google.com/o/oauth2/iframe",
                "cookie": cookies,
            },
        ) as response:
            result = await response.json()
            self.save_response(response=result, name="access_token")

            if "error" in result:
                if result["error"] == "invalid_grant":
                    raise BadCredentialsException(result["error"])

                raise Exception(result["error"])

            self.auth = GoogleAuthResponseForCookies(**result)

            return self.auth

    async def authenticate(self, access_token: str) -> NestResponse:
        """Start a new Nest session with an access token."""

        async with self.session.post(
            NEST_AUTH_URL_JWT,
            data=FormData(
                {
                    "embed_google_oauth_access_token": True,
                    "expire_after": "3600s",
                    "google_oauth_access_token": access_token,
                    "policy_id": "authproxy-oauth-policy",
                }
            ),
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": USER_AGENT,
                "Referer": self.environment.host,
            },
        ) as response:
            result = await response.json()
            self.save_response(response=result, name="authenticate")
            nest_auth = NestAuthResponse(**result)

        if nest_auth.jwt:
            _LOGGER.debug(f"JWT available: {nest_auth.jwt}")
            async with self.session.get(
                self.environment.host + "/session",
                headers={
                    "Authorization": f"Basic {nest_auth.jwt}",
                    "cookie": f"G_ENABLED_IDPS=google; eu_cookie_accepted=1; viewer-volume=0.5; cztoken={nest_auth.jwt}",
                },
            ) as response:
                try:
                    nest_response = await response.json()
                    self.save_response(response=nest_response, name="session")
                except ContentTypeError as exception:
                    nest_response = await response.text()

                    raise NestException(
                        f"{response.status} error while authenticating - {nest_response}. Please create an issue on GitHub."
                    ) from exception

                # Change variable names since Python cannot handle vars that start with a number
                if nest_response.get("2fa_state"):
                    nest_response["_2fa_state"] = nest_response.pop("2fa_state")
                if nest_response.get("2fa_enabled"):
                    nest_response["_2fa_enabled"] = nest_response.pop("2fa_enabled")
                if nest_response.get("2fa_state_changed"):
                    nest_response["_2fa_state_changed"] = nest_response.pop(
                        "2fa_state_changed"
                    )

                if nest_response.get("error"):
                    _LOGGER.error("Authnetication error: %s", nest_response.get("error"))

                try:
                    self.nest_session = NestResponse(**nest_response)
                except Exception as exception:
                    nest_response = await response.text()

                    if result.get("error"):
                        _LOGGER.error("Could not interprete Nest response")

                    raise NestException(
                        f"{response.status} error while authenticating - {nest_response}. Please create an issue on GitHub."
                    ) from exception

                return self.nest_session
        else:
            _LOGGER.warning("No JWT available, unable to start new session")
            return self.nest_session

    async def get_first_data(self, nest_access_token: str, user_id: str) -> Any:
        """Get first data."""
        _LOGGER.debug(f"Access token for first data: {nest_access_token}")
        async with self.session.post(
            APP_LAUNCH_URL_FORMAT.format(host=self.environment.host, user_id=user_id),
            headers={
                "Authorization": f"Basic {nest_access_token}",
                "X-nl-user-id": user_id,
                "X-nl-protocol-version": str(1),
            },
            json=NEST_REQUEST,
        ) as response:
            result = await response.json()
            self.save_response(response=result, name="first_data")

            if result.get("error"):
                _LOGGER.debug(result)

            self.transport_url = result["service_urls"]["urls"]["transport_url"]

            return result

    async def subscribe_for_data(
        self,
        nest_access_token: str,
        user_id: str,
        transport_url: str,
        updated_buckets: dict,
    ) -> Any:
        """Subscribe for data."""
        _LOGGER.debug(f"Got access token: {nest_access_token}")

        timeout = 3600 * 24

        objects = []
        for bucket in updated_buckets:
            objects.append(
                {
                    "object_key": bucket["object_key"],
                    "object_revision": bucket["object_revision"],
                    "object_timestamp": bucket["object_timestamp"],
                }
            )

        # TODO throw better exceptions
        async with self.session.post(
            f"{transport_url}/v6/subscribe",
            headers={
                "Authorization": f"Basic {nest_access_token}",
                "X-nl-user-id": user_id,
                "X-nl-protocol-version": str(1),
            },
            json={
                "objects": objects,
                # "timeout": timeout,
                # "sessionID": f"ios-${user_id}.{random}.{epoch}",
            },
            timeout=ClientTimeout(total=timeout),
        ) as response:
            _LOGGER.debug("Got data from Nest service %s", response.status)

            if response.status == 401:
                raise NotAuthenticatedException(await response.text())

            if response.status == 504:
                raise GatewayTimeoutException(await response.text())

            if response.status == 502:
                raise BadGatewayException(await response.text())

            try:
                result = await response.json()
                self.save_response(response=result, name="subscribe")
            except ContentTypeError as error:
                raise NestException(
                    "{} error ({}) while subscribing for data".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

            # TODO type object
            return result

    async def update_objects(
        self,
        objects_to_update: dict,
    ) -> Any:
        """Update objects."""

        if not self.nest_session or self.nest_session.is_expired():

            if not self.auth or self.auth.is_expired():
                await self.get_access_token()

            await self.authenticate(self.auth.access_token)

        epoch = int(time.time())
        random = str(randint(100, 999))

        # TODO throw better exceptions
        async with self.session.post(
            f"{self.transport_url}/v6/put",
            json={
                "session": f"ios-${self.nest_session.userid}.{random}.{epoch}",
                "objects": objects_to_update,
            },
            headers={
                "Authorization": f"Basic {self.nest_session.access_token}",
                "X-nl-user-id": self.nest_session.userid,
                "X-nl-protocol-version": str(1),
            },
        ) as response:
            if response.status == 401:
                raise NotAuthenticatedException(await response.text())

            try:
                result = await response.json()
                self.save_response(response=result, name="put")
            except ContentTypeError:
                raise NestException(
                    "{} error ({}) while updating objects".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

            # TODO type object

            return result

    async def get_camera_alerts(
        self,
        uuid: str,
        alert_interval: int = 60,
    ) -> Any:
        """Get alerts from camera."""
        if not self.nest_session or self.nest_session.is_expired():

            if not self.auth or self.auth.is_expired():
                await self.get_access_token()

            await self.authenticate(self.auth.access_token)

        _LOGGER.debug(f"Getting alerts for: {uuid}")
        alert_start_time = int(time.time() - alert_interval)
        async with self.session.get(
            f"https://nexusapi-us1.camera.home.nest.com/cuepoint/{uuid}/2",
            headers={
                "Authorization": f"Basic {self.nest_session.access_token}",
            },
            params={
                "start_time": alert_start_time,
            },
        ) as response:
            if response.status == 401:
                raise NotAuthenticatedException(await response.text())
            try:
                result = await response.json()
                self.save_response(response=result, name=f"alerts_{uuid}", append_response=False)
                return result
            except ContentTypeError:
                raise NestException(
                    "{} error ({}) while getting alerts".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

    async def get_camera_event_snapshot(
        self,
        uuid: str,
        cuepoint: int,
        height: int,
        nexus_api_nest_domain_host: str = "nexusapi-us1.camera.home.nest.com",
    ) -> Any:
        """Get event snapshot from camera."""
        if not self.nest_session or self.nest_session.is_expired():

            if not self.auth or self.auth.is_expired():
                await self.get_access_token()

            await self.authenticate(self.auth.access_token)

        _LOGGER.debug(f"Getting event snapshot for: {uuid}")
        async with self.session.get(
            f"https://{nexus_api_nest_domain_host}/get_event_clip",
            headers={
                "cookie": f"user_token={self.nest_session.access_token}",
            },
            params={
                "uuid": uuid,
                "cuepoint_id": cuepoint,
                "num_frames": 1,
                "height": height,
                "format": "sprite",
            },
        ) as response:
            if response.status == 401:
                raise NotAuthenticatedException(await response.text())
            try:
                return await response.read()
            except ContentTypeError:
                raise NestException(
                    "{} error ({}) while getting event snapshot".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

    async def get_camera_properties(
        self,
        uuid: str,
    ) -> Any:
        """Get properties from camera."""
        if not self.nest_session or self.nest_session.is_expired():

            if not self.auth or self.auth.is_expired():
                await self.get_access_token()

            await self.authenticate(self.auth.access_token)

        _LOGGER.debug(f"Getting properties for: {uuid}")
        async with self.session.get(
            f"https://webapi.camera.home.nest.com/api/cameras.get_with_properties",
            headers={
                "cookie": f"user_token={self.nest_session.access_token}",
            },
            params={
                "uuid": uuid,
            },
        ) as response:
            if response.status == 401:
                raise NotAuthenticatedException(await response.text())
            try:
                result = await response.json()
                self.save_response(response=result, name=f"properties_{uuid}")
                return result
            except ContentTypeError:
                raise NestException(
                    "{} error ({}) while getting properties".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

    async def get_camera_snapshot(
        self,
        uuid: str,
        nexus_api_nest_domain_host: str = "nexusapi-us1.camera.home.nest.com",
    ) -> Any:
        """Get snapshot from camera."""
        if not self.nest_session or self.nest_session.is_expired():

            if not self.auth or self.auth.is_expired():
                await self.get_access_token()

            await self.authenticate(self.auth.access_token)

        _LOGGER.debug(f"Getting snapshot for: {uuid}")
        async with self.session.get(
            f"https://{nexus_api_nest_domain_host}/get_image",
            headers={
                "cookie": f"user_token={self.nest_session.access_token}",
            },
            params={
                "uuid": uuid,
            },
        ) as response:
            if response.status == 401:
                raise NotAuthenticatedException(await response.text())
            try:
                return await response.read()
            except ContentTypeError:
                raise NestException(
                    "{} error ({}) while getting snapshot".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

    async def get_camera_zones(
        self,
        uuid: str,
        nexus_api_nest_domain_host: str = "nexusapi-us1.camera.home.nest.com",
    ) -> Any:
        """Get properties from camera."""
        if not self.nest_session or self.nest_session.is_expired():

            if not self.auth or self.auth.is_expired():
                await self.get_access_token()

            await self.authenticate(self.auth.access_token)

        _LOGGER.debug(f"Getting zones for: {uuid}")
        async with self.session.get(
            f"https://{nexus_api_nest_domain_host}/cuepoint_category/{uuid}",
            headers={
                "cookie": f"user_token={self.nest_session.access_token}",
            },
        ) as response:
            if response.status == 401:
                raise NotAuthenticatedException(await response.text())
            try:
                result = await response.json()
                self.save_response(response=result, name=f"zones_{uuid}")
                return result
            except ContentTypeError:
                raise NestException(
                    "{} error ({}) while getting zones".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

    async def get_weather(
        self,
        postal_code: int,
    ) -> Any:
        """Get weather data."""
        _LOGGER.debug(f"Getting weather for: {postal_code}")
        async with self.session.get(
            f"https://apps-weather.nest.com/weather/v1",
            params={
                "query": postal_code,
            },
        ) as response:
            if response.status == 401:
                raise NotAuthenticatedException(await response.text())
            try:
                result = await response.json()
                self.save_response(response=result, name=f"weather_{postal_code}")
                return result.get(str(postal_code))
            except ContentTypeError:
                raise NestException(
                    "{} error ({}) while getting weather".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

    async def set_camera_property(
        self,
        uuid: str,
        key: str,
        value: Any,
    ) -> Any:
        """Get properties from camera."""
        if not self.nest_session or self.nest_session.is_expired():

            if not self.auth or self.auth.is_expired():
                await self.get_access_token()

            await self.authenticate(self.auth.access_token)

        _LOGGER.debug(f"Setting property: {key} to: {value} for: {uuid}")
        async with self.session.post(
            f"https://webapi.camera.home.nest.com/api/dropcams.set_properties",
            headers={
                "cookie": f"user_token={self.nest_session.access_token}",
            },
            params={
                "uuid": uuid,
                key: value,
            },
        ) as response:
            if response.status == 401:
                raise NotAuthenticatedException(await response.text())
            try:
                result = await response.json()
                self.save_response(response=result, name=f"set_propertiy_{uuid}_{key}_{value}")
                return result
            except ContentTypeError:
                raise NestException(
                    "{} error ({}) while setting properties".format(
                        response.status,
                        HTTPStatus(response.status).phrase,
                    )
                )

    def save_response(
        self,
        response: dict[str, Any],
        name: str = "response",
        append_response: bool = False,
    ) -> None:
        if self.save_response_enabled and response:
            if not os.path.isdir(SAVE_RESPONSE_LOCATION):
                os.mkdir(SAVE_RESPONSE_LOCATION)
            name = name.replace("/", "_").replace(".", "_")
            path = f"{SAVE_RESPONSE_LOCATION}/{name}.json"
            with open(path, "w") as file:
                data = response
                if append_response:
                    data = json.load(file)
                    if isinstance(data, list) and isinstance(response, list):
                        data.extend(response)
                json.dump(data, file, default=lambda o: "not-serializable", indent=4, sort_keys=True)
            file.close()
