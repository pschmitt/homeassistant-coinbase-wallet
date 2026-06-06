"""Config flow for Coinbase Wallet."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import CoinbaseWalletApiClient
from .const import CONF_API_KEY_NAME, CONF_API_PRIVATE_KEY, DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL
from .exceptions import CoinbaseWalletAuthError, CoinbaseWalletConnectionError

_LOGGER = logging.getLogger(__name__)


async def _validate(hass: HomeAssistant, data: dict[str, Any]) -> None:
    client = CoinbaseWalletApiClient(
        key_name=data[CONF_API_KEY_NAME],
        private_key_pem=data[CONF_API_PRIVATE_KEY],
    )
    await hass.async_add_executor_job(client.validate)


def _build_schema(
    defaults: dict[str, Any],
    *,
    key_required: bool = True,
    show_name: bool = True,
) -> vol.Schema:
    fields: dict[vol.Marker, Any] = {
        vol.Required(
            CONF_API_KEY_NAME, default=defaults.get(CONF_API_KEY_NAME, "")
        ): TextSelector(),
    }
    if key_required:
        fields[vol.Required(CONF_API_PRIVATE_KEY, default=defaults.get(CONF_API_PRIVATE_KEY, ""))] = TextSelector(
            TextSelectorConfig(multiline=True, type=TextSelectorType.PASSWORD)
        )
    else:
        fields[vol.Optional(CONF_API_PRIVATE_KEY)] = TextSelector(
            TextSelectorConfig(multiline=True, type=TextSelectorType.PASSWORD)
        )
    if show_name:
        fields[vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, "Coinbase Wallet"))] = TextSelector()
    return vol.Schema(fields)


class CoinbaseWalletConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Coinbase Wallet."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> CoinbaseWalletOptionsFlow:
        return CoinbaseWalletOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {
                CONF_API_KEY_NAME: user_input[CONF_API_KEY_NAME].strip(),
                CONF_API_PRIVATE_KEY: user_input[CONF_API_PRIVATE_KEY],
            }
            name = user_input.get(CONF_NAME) or "Coinbase Wallet"
            try:
                await _validate(self.hass, data)
            except CoinbaseWalletAuthError:
                errors["base"] = "invalid_auth"
            except CoinbaseWalletConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Coinbase Wallet config validation")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"coinbase_wallet:{data[CONF_API_KEY_NAME]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data=data,
                    options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema({}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            private_key = user_input.get(CONF_API_PRIVATE_KEY) or entry.data[CONF_API_PRIVATE_KEY]
            merged = {
                **entry.data,
                CONF_API_KEY_NAME: user_input[CONF_API_KEY_NAME].strip(),
                CONF_API_PRIVATE_KEY: private_key,
            }
            name = user_input.get(CONF_NAME) or entry.title
            try:
                await _validate(self.hass, merged)
            except CoinbaseWalletAuthError:
                errors["base"] = "invalid_auth"
            except CoinbaseWalletConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Coinbase Wallet reconfigure validation")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(entry, title=name, data=merged)

        defaults = {**entry.data, CONF_NAME: entry.title}
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_build_schema(defaults, key_required=False),
            errors=errors,
        )


class CoinbaseWalletOptionsFlow(OptionsFlow):
    """Handle options for Coinbase Wallet."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            mode=NumberSelectorMode.BOX,
                            step=1,
                        )
                    )
                }
            ),
        )
