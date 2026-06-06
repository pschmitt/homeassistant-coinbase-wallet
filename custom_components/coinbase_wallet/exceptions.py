"""Exceptions for the Coinbase Wallet integration."""

from __future__ import annotations


class CoinbaseWalletError(Exception):
    """Base exception for Coinbase Wallet errors."""


class CoinbaseWalletConnectionError(CoinbaseWalletError):
    """Raised when the Coinbase API cannot be reached."""


class CoinbaseWalletAuthError(CoinbaseWalletError):
    """Raised when Coinbase API authentication fails."""


class CoinbaseWalletApiError(CoinbaseWalletError):
    """Raised when the Coinbase API returns an error response."""
