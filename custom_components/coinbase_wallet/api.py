"""Coinbase CDP API client."""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests

from .const import DEFAULT_REQUEST_TIMEOUT, MAX_TRANSACTIONS
from .exceptions import CoinbaseWalletApiError, CoinbaseWalletAuthError, CoinbaseWalletConnectionError

_LOGGER = logging.getLogger(__name__)

_API_BASE = "https://api.coinbase.com"


def _make_jwt(key_name: str, private_key_pem: str, method: str, path: str) -> str:
    """Create a short-lived CDP JWT for one API request."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)

    def _b64url(data: dict | bytes) -> str:
        if isinstance(data, dict):
            data = json.dumps(data, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    now = int(time.time())
    header = {"alg": "ES256", "kid": key_name, "nonce": os.urandom(16).hex(), "typ": "JWT"}
    claims = {
        "sub": key_name,
        "iss": "cdp",
        "nbf": now,
        "exp": now + 120,
        "uri": f"{method} api.coinbase.com{path}",
    }
    signing_input = f"{_b64url(header)}.{_b64url(claims)}".encode()
    sig_der = key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(sig_der)
    sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"{_b64url(header)}.{_b64url(claims)}.{_b64url(sig)}"


def _serialize_transaction(tx: dict[str, Any]) -> dict[str, Any]:
    """Flatten a Coinbase v2 transaction object to a simple dict."""
    amount = tx.get("amount") or {}
    native = tx.get("native_amount") or {}
    network = tx.get("network") or {}

    def _simplify_party(p: Any) -> str | None:
        if not isinstance(p, dict):
            return None
        resource = p.get("resource", "")
        if resource == "email":
            return p.get("email")
        if resource == "user":
            return p.get("name") or p.get("resource_path")
        return p.get("address") or resource or None

    details = tx.get("details") or {}
    description = tx.get("description") or details.get("title") or ""

    return {
        "id": tx.get("id", ""),
        "type": tx.get("type", ""),
        "status": tx.get("status", ""),
        "amount": float(amount.get("amount", 0)),
        "currency": amount.get("currency", ""),
        "native_amount": float(native.get("amount", 0)),
        "native_currency": native.get("currency", "EUR"),
        "description": description,
        "created_at": tx.get("created_at", ""),
        "to": _simplify_party(tx.get("to")),
        "from": _simplify_party(tx.get("from")),
        "network_hash": network.get("hash", ""),
    }


@dataclass
class CoinbaseWalletData:
    """Represents one Coinbase wallet/account."""

    account_id: str
    account_name: str
    currency: str
    balance: float
    transactions: list[dict[str, Any]] = field(default_factory=list)


class CoinbaseWalletApiClient:
    """Client for the Coinbase v2 REST API using CDP JWT authentication."""

    def __init__(self, key_name: str, private_key_pem: str) -> None:
        self._key_name = key_name
        # Accept both real newlines and escaped \n from HA secrets.yaml
        self._private_key_pem = private_key_pem.replace("\\n", "\n")

    def _get(self, path: str) -> dict[str, Any]:
        """Issue an authenticated GET request."""
        try:
            token = _make_jwt(self._key_name, self._private_key_pem, "GET", path)
        except Exception as exc:
            raise CoinbaseWalletAuthError(f"JWT signing failed: {exc}") from exc

        try:
            resp = requests.get(
                f"{_API_BASE}{path}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise CoinbaseWalletConnectionError(str(exc)) from exc

        if resp.status_code == 401:
            raise CoinbaseWalletAuthError(f"401 Unauthorized for {path}")
        if not resp.ok:
            raise CoinbaseWalletApiError(f"HTTP {resp.status_code} for {path}: {resp.text[:200]}")
        return resp.json()

    def fetch_data(self) -> dict[str, CoinbaseWalletData]:
        """Fetch all non-empty wallets with their recent transactions."""
        data = self._get("/v2/accounts?limit=100")
        result: dict[str, CoinbaseWalletData] = {}

        for acct in data.get("data", []):
            balance = float(acct["balance"]["amount"])
            if balance <= 0:
                continue
            account_id = acct["id"]
            currency = acct["balance"]["currency"]
            transactions = self._fetch_transactions(account_id, currency)

            result[account_id] = CoinbaseWalletData(
                account_id=account_id,
                account_name=acct.get("name", currency),
                currency=currency,
                balance=balance,
                transactions=transactions,
            )

        return result

    def _fetch_transactions(self, account_id: str, currency: str) -> list[dict[str, Any]]:
        try:
            data = self._get(f"/v2/accounts/{account_id}/transactions?limit={MAX_TRANSACTIONS}")
            return [_serialize_transaction(tx) for tx in data.get("data", [])]
        except Exception as exc:
            _LOGGER.warning(
                "Failed to fetch transactions for %s account %s: %s", currency, account_id, exc
            )
            return []

    def validate(self) -> dict[str, CoinbaseWalletData]:
        """Validate credentials by performing a real API call."""
        return self.fetch_data()
