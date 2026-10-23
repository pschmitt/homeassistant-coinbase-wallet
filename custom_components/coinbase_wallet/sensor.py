"""Sensor platform for Coinbase Wallet account balances."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CoinbaseWalletData
from .const import (
    CURRENCY_ICONS,
    CURRENCY_PRECISION,
    DEFAULT_ICON,
    DEFAULT_PRECISION,
    DOMAIN,
    FIAT_CURRENCIES,
)
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
        for account_id, wallet in (coordinator.data or {}).items():
            if account_id in known_accounts:
                continue
            known_accounts.add(account_id)
            new.append(CoinbaseBalanceSensor(coordinator=coordinator, wallet=wallet))
            if wallet.currency not in FIAT_CURRENCIES:
                new.append(CoinbaseProfitLossSensor(coordinator=coordinator, wallet=wallet))
        if new:
            async_add_entities(new)

    _add_missing()
    config_entry.async_on_unload(coordinator.async_add_listener(_add_missing))


class CoinbaseBalanceSensor(CoinbaseWalletEntity, SensorEntity):
    """Sensor for the balance of one Coinbase wallet."""

    _attr_state_class = SensorStateClass.TOTAL
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
        if wallet.currency in FIAT_CURRENCIES:
            self._attr_device_class = SensorDeviceClass.MONETARY

    @property
    def _wallet(self) -> CoinbaseWalletData | None:
        return (self.coordinator.data or {}).get(self._account_id)

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


class CoinbaseProfitLossSensor(CoinbaseBalanceSensor):
    """Coinbase-reported unrealized gain or loss for one crypto wallet."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: CoinbaseWalletCoordinator,
        wallet: CoinbaseWalletData,
    ) -> None:
        super().__init__(coordinator, wallet)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}:{wallet.account_id}:pnl"
        self._attr_name = f"{wallet.currency} PnL"
        self._attr_icon = "mdi:chart-line"
        self._attr_suggested_display_precision = 2
        self._attr_native_unit_of_measurement = None

    @property
    def _position(self) -> dict[str, Any]:
        wallet = self._wallet
        return (wallet.position or {}) if wallet else {}

    @property
    def available(self) -> bool:
        return (
            super().available
            and self._position.get("unrealized_pnl") is not None
            and bool(self.native_unit_of_measurement)
        )

    @property
    def native_unit_of_measurement(self) -> str | None:
        return (self._position.get("cost_basis") or {}).get("currency")

    @property
    def native_value(self) -> float | None:
        value = self._position.get("unrealized_pnl")
        return float(value) if value is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        position = self._position
        basis = (position.get("cost_basis") or {}).get("value")
        average = (position.get("average_entry_price") or {}).get("value")
        cost = float(basis) if basis is not None else None
        pnl = self.native_value
        return {
            "account_id": self._account_id,
            "pnl_type": "unrealized",
            "source": "Coinbase portfolio breakdown",
            "cost_basis": cost,
            "average_buy_in": float(average) if average is not None else None,
            "market_value": position.get("total_balance_fiat"),
            "gain_loss_percent": round(pnl / cost * 100, 2) if pnl is not None and cost else None,
        }
