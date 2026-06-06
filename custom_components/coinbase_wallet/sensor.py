"""Sensor platform for Coinbase Wallet account balances."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CoinbaseWalletData
from .const import CURRENCY_ICONS, CURRENCY_PRECISION, DEFAULT_ICON, DEFAULT_PRECISION, DOMAIN
from .coordinator import CoinbaseWalletCoordinator
from .entity import CoinbaseWalletEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coinbase Wallet balance sensors from a config entry."""
    coordinator: CoinbaseWalletCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    known_accounts: set[str] = set()

    @callback
    def _add_missing() -> None:
        new: list[SensorEntity] = []
        for account_id, wallet in coordinator.data.items():
            if account_id in known_accounts:
                continue
            known_accounts.add(account_id)
            new.append(CoinbaseBalanceSensor(coordinator=coordinator, wallet=wallet))
        if new:
            async_add_entities(new)

    _add_missing()
    config_entry.async_on_unload(coordinator.async_add_listener(_add_missing))


class CoinbaseBalanceSensor(CoinbaseWalletEntity, SensorEntity):
    """Sensor for the balance of one Coinbase wallet."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _unrecorded_attributes = frozenset({"transactions"})

    def __init__(
        self,
        coordinator: CoinbaseWalletCoordinator,
        wallet: CoinbaseWalletData,
    ) -> None:
        super().__init__(coordinator)
        self._account_id = wallet.account_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}:{wallet.account_id}:balance"
        self._attr_name = wallet.currency
        self._attr_native_unit_of_measurement = wallet.currency
        self._attr_icon = CURRENCY_ICONS.get(wallet.currency, DEFAULT_ICON)
        self._attr_suggested_display_precision = CURRENCY_PRECISION.get(
            wallet.currency, DEFAULT_PRECISION
        )

    @property
    def _wallet(self) -> CoinbaseWalletData | None:
        return self.coordinator.data.get(self._account_id)

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self._wallet is not None

    @property
    def native_value(self) -> float | None:
        w = self._wallet
        return w.balance if w else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        w = self._wallet
        if w is None:
            return {}
        attrs: dict[str, Any] = {
            "account_id": w.account_id,
            "account_name": w.account_name,
            "transactions": w.transactions,
        }
        if w.address is not None:
            attrs["address"] = w.address
        return attrs
