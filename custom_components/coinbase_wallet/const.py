"""Constants for the Coinbase Wallet integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "coinbase_wallet"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_API_KEY_NAME = "api_key_name"
CONF_API_PRIVATE_KEY = "api_private_key"

DEFAULT_SCAN_INTERVAL = 3600
MIN_SCAN_INTERVAL = 300
DEFAULT_REQUEST_TIMEOUT = 30
MAX_TRANSACTIONS = 50

REPAIR_AUTH_FAILED = "auth_failed"
REPAIR_CANNOT_CONNECT = "cannot_connect"

CURRENCY_ICONS: dict[str, str] = {
    "BTC": "mdi:bitcoin",
    "ETH": "mdi:ethereum",
    "EUR": "mdi:currency-eur",
    "EURC": "mdi:currency-eur",
    "USDC": "mdi:currency-usd",
    "SOL": "mdi:cash",
}
CURRENCY_PRECISION: dict[str, int] = {
    "BTC": 8,
    "ETH": 6,
    "EUR": 2,
    "EURC": 2,
    "USDC": 2,
}
DEFAULT_ICON = "mdi:cash"
DEFAULT_PRECISION = 4
