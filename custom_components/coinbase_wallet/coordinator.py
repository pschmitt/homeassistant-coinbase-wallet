"""Data update coordinator for Coinbase Wallet."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CoinbaseWalletApiClient, CoinbaseWalletData
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, REPAIR_AUTH_FAILED, REPAIR_CANNOT_CONNECT
from .exceptions import CoinbaseWalletAuthError, CoinbaseWalletConnectionError

_LOGGER = logging.getLogger(__name__)


class CoinbaseWalletCoordinator(DataUpdateCoordinator[dict[str, CoinbaseWalletData]]):
    """Coordinate periodic fetches for one Coinbase account."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CoinbaseWalletApiClient,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(
                seconds=config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = client
        self.config_entry = config_entry

    async def _async_update_data(self) -> dict[str, CoinbaseWalletData]:
        auth_issue = f"{REPAIR_AUTH_FAILED}_{self.config_entry.entry_id}"
        conn_issue = f"{REPAIR_CANNOT_CONNECT}_{self.config_entry.entry_id}"
        name = self.config_entry.title

        try:
            data = await self.hass.async_add_executor_job(self.client.fetch_data)
        except CoinbaseWalletAuthError as err:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                auth_issue,
                is_fixable=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key=REPAIR_AUTH_FAILED,
                translation_placeholders={"account_name": name},
            )
            raise UpdateFailed(f"Coinbase auth failed for {name}: {err}") from err
        except (CoinbaseWalletConnectionError, Exception) as err:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                conn_issue,
                is_fixable=True,
                severity=ir.IssueSeverity.WARNING,
                translation_key=REPAIR_CANNOT_CONNECT,
                translation_placeholders={"account_name": name},
            )
            raise UpdateFailed(f"Coinbase connection error for {name}: {err}") from err

        ir.async_delete_issue(self.hass, DOMAIN, auth_issue)
        ir.async_delete_issue(self.hass, DOMAIN, conn_issue)
        return data
