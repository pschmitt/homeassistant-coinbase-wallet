"""Base entity for Coinbase Wallet."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoinbaseWalletCoordinator


class CoinbaseWalletEntity(CoordinatorEntity[CoinbaseWalletCoordinator]):
    """Base entity for all Coinbase Wallet sensors."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        entry = self.coordinator.config_entry
        return DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Coinbase",
            model="Coinbase CDP",
            configuration_url="https://www.coinbase.com/settings/api",
        )
