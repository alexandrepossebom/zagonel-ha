"""DataUpdateCoordinator for Zagonel Smart Shower."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import httpx

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BASE_URL, SCAN_INTERVAL, parse_measure

_LOGGER = logging.getLogger(__name__)


class ZagonelCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch data from Zagonel API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Zagonel",
            update_interval=SCAN_INTERVAL,
        )
        self.config_entry = entry
        self._client: httpx.AsyncClient | None = None
        self._token: str = entry.data["token"]
        self._user_id: str = entry.data["userId"]
        self._energy_price: float = entry.data.get("energyPrice", 0)
        self._water_price: float = entry.data.get("waterPrice", 0)

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    @staticmethod
    def _create_client() -> httpx.AsyncClient:
        """Create httpx client (blocks on SSL cert loading)."""
        return httpx.AsyncClient(base_url=BASE_URL, timeout=15)

    async def _async_get_client(self) -> httpx.AsyncClient:
        """Lazy-init the HTTP client off the event loop."""
        if self._client is None:
            self._client = await self.hass.async_add_executor_job(self._create_client)
        return self._client

    async def _async_re_authenticate(self) -> None:
        """Re-authenticate to get a fresh token."""
        try:
            client = await self._async_get_client()
            resp = await client.post(
                "/users/login",
                json={
                    "email": self.config_entry.data[CONF_EMAIL],
                    "password": self.config_entry.data[CONF_PASSWORD],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as err:
            raise ConfigEntryAuthFailed("Login credentials expired") from err
        except (httpx.ConnectError, httpx.TimeoutException) as err:
            raise UpdateFailed("Cannot connect to Zagonel API") from err

        self._token = data["token"]
        self._energy_price = data.get("energyPrice", self._energy_price)
        self._water_price = data.get("waterPrice", self._water_price)

        # Persist updated token
        new_data = {**self.config_entry.data, "token": self._token}
        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch showers and measurements from the API."""
        try:
            return await self._fetch_data()
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 401:
                await self._async_re_authenticate()
                return await self._fetch_data()
            raise UpdateFailed(f"API error: {err.response.status_code}") from err
        except (httpx.ConnectError, httpx.TimeoutException) as err:
            raise UpdateFailed("Cannot connect to Zagonel API") from err

    async def _fetch_data(self) -> dict[str, Any]:
        """Perform the actual API calls."""
        # Get showers
        client = await self._async_get_client()
        resp = await client.get(f"/showers/user/{self._user_id}", headers=self._headers)
        resp.raise_for_status()
        showers = resp.json().get("showers", [])

        # Timestamp for first day of current month
        now = datetime.now(tz=timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        ts_start = int(month_start.timestamp() * 1000)

        result: dict[str, Any] = {}

        for shower in showers:
            shower_id = shower["id"]
            resp = await client.get(
                f"/measures/shower/{shower_id}/{ts_start}", headers=self._headers
            )
            resp.raise_for_status()
            measures_raw = resp.json()
            if isinstance(measures_raw, dict):
                measures_raw = measures_raw.get("measures", [])

            measures = [
                parse_measure(m, self._energy_price, self._water_price)
                for m in measures_raw
            ]

            result[shower_id] = {
                "shower": shower,
                "measures": measures,
            }

        return result

    async def async_shutdown(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
        await super().async_shutdown()
