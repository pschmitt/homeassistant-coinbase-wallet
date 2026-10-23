"""The Coinbase Wallet integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import CoinbaseWalletApiClient
from .const import CONF_API_KEY_NAME, CONF_API_PRIVATE_KEY, DOMAIN, PLATFORMS
from .coordinator import CoinbaseWalletCoordinator


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Coinbase Wallet from a config entry."""
    client = CoinbaseWalletApiClient(
        key_name=config_entry.data[CONF_API_KEY_NAME],
        private_key_pem=config_entry.data[CONF_API_PRIVATE_KEY],
    )
    coordinator = CoinbaseWalletCoordinator(hass, client, config_entry)

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    if coordinator.data is None:
        coordinator.last_update_success = False
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    config_entry.async_on_unload(config_entry.add_update_listener(async_update_listener))
    config_entry.async_create_background_task(
        hass, coordinator.async_refresh(), "coinbase_wallet_first_refresh"
    )
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a Coinbase Wallet config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok


async def async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(config_entry.entry_id)
