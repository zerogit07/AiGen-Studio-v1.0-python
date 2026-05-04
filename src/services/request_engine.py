"""Resilient HTTP request engine using aiohttp with key/proxy rotation."""
from __future__ import annotations

import logging
import os
import random
from typing import Any

import aiohttp

from src.core.constants import FINGERPRINTS
from src.database.apikeys import api_key_manager

logger = logging.getLogger(__name__)

FREEPIK_API_BASE = os.getenv("FREEPIK_API_BASE", "https://api.freepik.com/v1/ai")

_client_pool: dict[str, aiohttp.ClientSession] = {}


async def _get_session(proxy: str) -> aiohttp.ClientSession:
    key = proxy or "__direct__"
    if key not in _client_pool:
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=60, connect=20, sock_read=20)
        _client_pool[key] = aiohttp.ClientSession(connector=connector, timeout=timeout)
    return _client_pool[key]


async def cleanup_sessions() -> None:
    for session in _client_pool.values():
        await session.close()
    _client_pool.clear()


async def _request_once(
    method: str,
    url: str,
    api_key: str,
    proxy: str = "",
    fingerprint: dict | None = None,
    payload: dict | None = None,
) -> dict[str, Any]:
    headers = {
        "x-freepik-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if fingerprint:
        headers.update(fingerprint)

    session = await _get_session(proxy)
    try:
        kwargs: dict[str, Any] = {"headers": headers}
        if proxy:
            kwargs["proxy"] = proxy
        if method.upper() == "POST" and payload:
            kwargs["json"] = payload

        async with session.request(method, url, **kwargs) as response:
            status = response.status
            data = await response.json()

            if status in (403, 429):
                return {"error": "burned", "status": status, "data": data}
            if status == 401:
                return {"error": "dead_key", "status": status, "data": data}
            if status >= 500:
                return {"error": "server_error", "status": status, "data": data}
            if status >= 400:
                return {"error": "client_error", "status": status, "data": data}

            return {"data": data, "status": status}

    except aiohttp.ClientError as exc:
        return {"error": "network", "message": str(exc)}
    except Exception as exc:
        return {"error": "unknown", "message": str(exc)}


async def request_engine(
    method: str,
    endpoint: str,
    payload: dict | None = None,
    api_key: str | None = None,
    proxy: str = "",
    max_retries: int = 3,
) -> dict[str, Any]:
    url = f"{FREEPIK_API_BASE}/{endpoint}"

    if api_key:
        keys_to_try = [api_key]
    else:
        keys_to_try = api_key_manager.get_shuffled_active_keys()

    if not keys_to_try:
        return {"error": "no_keys", "message": "Tidak ada API key yang tersedia."}

    last_result = {}
    for attempt in range(max_retries):
        for key in keys_to_try:
            fp = random.choice(FINGERPRINTS)
            result = await _request_once(method, url, key, proxy, fp, payload)

            if "error" not in result:
                api_key_manager.update_index()
                return {**result, "used_key": key}

            error = result["error"]
            if error == "burned":
                logger.warning("Key burned (403/429): %s...", key[:12])
                await api_key_manager.set_cooldown(key, 1800)
                continue
            elif error == "dead_key":
                logger.warning("Dead key (401): %s...", key[:12])
                await api_key_manager.mark_key_dead(key)
                continue
            elif error in ("server_error", "network"):
                logger.warning("Retryable error on attempt %d: %s", attempt + 1, result.get("message", ""))
                last_result = result
                break

            last_result = result

    return last_result or {"error": "exhausted", "message": "Semua percobaan gagal."}
