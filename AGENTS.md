# Agent instructions

## Project

This Home Assistant integration connects to Coinbase's CDP API and exposes wallet balances, transaction history, and portfolio profit/loss as sensors.

## Working in this repository

- Read `README.md` before changing API permissions, wallet discovery, or account data handling.
- Treat wallet identifiers, transactions, balances, and credentials as sensitive; keep them out of source, logs, and fixtures.
- Before changing CI, check [pschmitt/ci-workflows](https://github.com/pschmitt/ci-workflows) for reusable components and preserve this repository's existing checks.

## Validation

- Run `uvx ruff check .` and `uvx ruff format --check .` for Python changes.
- CI runs Hassfest and the shared Ruff checks; it currently has no test job.
