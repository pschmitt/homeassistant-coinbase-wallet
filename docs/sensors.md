# Sensors

The integration creates one Home Assistant device per Coinbase account or API
key. Each non-empty wallet gets a balance sensor, such as `sensor.<name>_btc`,
`sensor.<name>_eth`, `sensor.<name>_eur` or `sensor.<name>_eurc`.
Balance sensors have `account_name`, `account_id` and `transactions` attributes;
the latter contains up to 50 recent transactions.

Each crypto wallet also has a `sensor.<name>_<currency>_pnl` sensor showing
unrealized profit or loss in the fiat currency returned by Coinbase. It has
`cost_basis`, `average_buy_in`, `market_value` and `gain_loss_percent`
attributes. P&L comes from Coinbase's Advanced Trade portfolio breakdown,
including staked holdings, rather than from transaction history. It excludes
realized gains from past sales. If portfolio data cannot be retrieved, for
example because the API key lacks portfolio read access, P&L becomes
unavailable while balances remain available.

Each transaction entry may contain:

| Field | Description |
|-------|-------------|
| `type` | `send`, `receive`, `buy`, `sell`, `fiat_deposit`, … |
| `status` | `completed`, `pending`, … |
| `amount` | Signed amount in the wallet's currency |
| `native_amount` | Signed fiat equivalent |
| `description` | Human-readable description |
| `created_at` | ISO 8601 timestamp |
| `to` / `from` | Counterparty, such as an email address or wallet address |
| `network_hash` | On-chain transaction hash, if available |
