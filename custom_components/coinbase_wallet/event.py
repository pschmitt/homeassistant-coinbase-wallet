"""Event platform for Coinbase Wallet — one event entity per wallet."""

from __future__ import annotations

import logging

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CoinbaseWalletData
from .const import DOMAIN
from .coordinator import CoinbaseWalletCoordinator
from .entity import CoinbaseWalletEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up per-wallet Coinbase last-transaction event entities."""
    coordinator: CoinbaseWalletCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]
    known_accounts: set[str] = set()

    @callback
    def _add_missing() -> None:
        new: list[CoinbaseWalletTransactionEvent] = []
        for account_id, wallet in (coordinator.data or {}).items():
            if account_id in known_accounts:
                continue
            known_accounts.add(account_id)
            new.append(CoinbaseWalletTransactionEvent(coordinator, wallet))
        if new:
            async_add_entities(new)

    _add_missing()
    config_entry.async_on_unload(coordinator.async_add_listener(_add_missing))


class CoinbaseWalletTransactionEvent(CoinbaseWalletEntity, EventEntity):
    """Event entity that fires when a new transaction arrives for one wallet."""

    _attr_event_types = ["transaction"]
    _attr_icon = "mdi:bank-transfer"

    def __init__(
        self,
        coordinator: CoinbaseWalletCoordinator,
        wallet: CoinbaseWalletData,
    ) -> None:
        super().__init__(coordinator)
        self._account_id = wallet.account_id
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}:{wallet.account_id}:last_transaction"
        )
        self._attr_name = f"{wallet.currency} Last transaction"
        self._last_tx_id: str | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        if not data:
            super()._handle_coordinator_update()
            return

        wallet = data.get(self._account_id)
        if wallet is None:
            super()._handle_coordinator_update()
            return

        latest = _latest_transaction(wallet)
        if latest is None:
            super()._handle_coordinator_update()
            return

        tx_id = latest.get("id")

        if self._last_tx_id is None:
            self._last_tx_id = tx_id
        elif tx_id is not None and tx_id != self._last_tx_id:
            self._last_tx_id = tx_id
            self._trigger_event(
                "transaction",
                {
                    "transaction_id": tx_id,
                    "type": latest.get("type"),
                    "status": latest.get("status"),
                    "amount": latest.get("amount"),
                    "currency": latest.get("currency"),
                    "native_amount": latest.get("native_amount"),
                    "native_currency": latest.get("native_currency"),
                    "description": latest.get("description"),
                    "created_at": latest.get("created_at"),
                    "network_hash": latest.get("network_hash"),
                },
            )
            return

        super()._handle_coordinator_update()


def _latest_transaction(wallet: CoinbaseWalletData) -> dict | None:
    best: dict | None = None
    best_created = ""
    for tx in (wallet.transactions or []):
        created = tx.get("created_at") or ""
        if created > best_created:
            best_created = created
            best = tx
    return best
