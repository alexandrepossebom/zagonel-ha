"""Config flow for Zagonel Smart Shower."""

from __future__ import annotations

import logging
from typing import Any

import httpx
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import BASE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ZagonelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zagonel."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: email + password login."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            try:
                async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
                    resp = await client.post(
                        "/users/login",
                        json={"email": email, "password": password},
                    )
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.HTTPStatusError:
                errors["base"] = "invalid_auth"
            except (httpx.ConnectError, httpx.TimeoutException):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(email.lower())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=data.get("userName", email),
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        "token": data["token"],
                        "userId": data["userId"],
                        "userName": data.get("userName", ""),
                        "energyPrice": data.get("energyPrice", 0),
                        "waterPrice": data.get("waterPrice", 0),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )
