# Coinbase Wallet for Home Assistant

`coinbase_wallet` is a Home Assistant custom integration that connects to your
[Coinbase](https://www.coinbase.com) account via the
[CDP API](https://portal.cdp.coinbase.com/access/api) and exposes wallet
balances and transaction history as sensor entities.

> **Note:** This integration coexists with the native `coinbase` HA integration
> (used for live exchange rates). They use different domains and do not conflict.

## Features

- One Home Assistant **device** per Coinbase account / API key
- One **balance sensor** per non-empty wallet (BTC, ETH, EUR, EURC, …), created dynamically
- Rich sensor attributes: `account_name`, `account_id`, `transactions` (last 50)
- Configurable via the HA UI — no YAML needed
- Options flow to adjust the poll interval
- Reconfigure flow to update API credentials without deleting the entry
- Raises repair issues on auth failures or connectivity problems

## Requirements

- A [Coinbase Developer Platform (CDP) API key](https://portal.cdp.coinbase.com/access/api)
  with at least **Wallet › Read** permission.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pschmitt&repository=homeassistant-coinbase-wallet&category=integration)

1. Click the badge above — or open HACS → Integrations → ⋮ → Custom repositories and add
   `https://github.com/pschmitt/homeassistant-coinbase-wallet` as type **Integration**.
2. Install **Coinbase Wallet**.
3. Restart Home Assistant.

### Manual

Copy `custom_components/coinbase_wallet/` into your Home Assistant `custom_components/` directory,
then restart.

## Configuration

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Coinbase Wallet**.
3. Fill in:
   - **API key name** — the key identifier from the CDP portal, in the form
     `organizations/{org-id}/apiKeys/{key-id}`.
   - **Private key (PEM)** — the EC private key PEM block. Paste the full block
     including `-----BEGIN EC PRIVATE KEY-----` and `-----END EC PRIVATE KEY-----`.
   - **Account name** — display name for the HA device (default: `Coinbase`).

## Sensors

One sensor is created per non-empty Coinbase wallet:

| Sensor | State | Key attributes |
|--------|-------|----------------|
| `sensor.<name>_btc` | BTC balance | `account_name`, `account_id`, `transactions` |
| `sensor.<name>_eth` | ETH balance | same |
| `sensor.<name>_eur` | EUR balance | same |
| `sensor.<name>_eurc` | EURC balance | same |
| `sensor.<name>_<currency>` | balance | same |

Transaction entries in the `transactions` attribute:

| Field | Description |
|-------|-------------|
| `type` | `send`, `receive`, `buy`, `sell`, `fiat_deposit`, … |
| `status` | `completed`, `pending`, … |
| `amount` | Amount in the wallet's native currency (signed) |
| `native_amount` | EUR equivalent (signed) |
| `description` | Human-readable description |
| `created_at` | ISO 8601 timestamp |
| `to` / `from` | Counterparty (email, address, or name) |
| `network_hash` | On-chain transaction hash (if applicable) |

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
