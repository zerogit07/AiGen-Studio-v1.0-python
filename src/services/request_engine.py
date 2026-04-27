from __future__ import annotations

import logging
import time

import httpx

from src.database.apikeys import api_key_manager
from src.database.proxies import proxy_manager

logger = logging.getLogger(__name__)


async def request_engine(
    method: str,
    url: str,
    headers: dict | None = None,
    json_data: dict | None = None,
    force_api_key: str | None = None,
) -> dict:
    """Resilient request wrapper with API key rotation and proxy support.

    Handles only documented Freepik API response codes:
    - 200: Success
    - 400: Bad Request (parameter invalid)
    - 401: Unauthorized (API key invalid/missing)
    - 500: Internal Server Error
    - 503: Service Unavailable
    """
    last_error: Exception | None = None
    now = int(time.time() * 1000)

    keys_to_try = []

    if force_api_key:
        forced = next(
            (
                k
                for k in api_key_manager.get_all_keys()
                if k.key == force_api_key and k.active and k.cooldown_until < now
            ),
            None,
        )
        if forced:
            keys_to_try.append(forced)

    rotated = api_key_manager.get_rotated_keys()
    for k in rotated:
        if not any(existing.key == k.key for existing in keys_to_try):
            keys_to_try.append(k)

    if not keys_to_try and force_api_key:
        forced = next(
            (
                k
                for k in api_key_manager.get_all_keys()
                if k.key == force_api_key and k.active
            ),
            None,
        )
        if forced:
            keys_to_try.append(forced)

    if not keys_to_try:
        raise RuntimeError("Semua API Key sedang sibuk atau tidak tersedia")

    for api_key_obj in keys_to_try:
        api_key = api_key_obj.key
        skip_to_next_key = False

        max_proxy_try = 3
        for _ in range(max_proxy_try):
            proxy_url = proxy_manager.get_rotated_proxy_url()
            try:
                req_headers = dict(headers or {})
                req_headers["x-freepik-api-key"] = api_key
                req_headers.setdefault("Content-Type", "application/json")

                logger.info(
                    "[Request] Key %s... %s",
                    api_key[:8],
                    "via Proxy" if proxy_url else "Direct",
                )
                async with httpx.AsyncClient(
                    timeout=15,
                    proxy=proxy_url,
                ) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=req_headers,
                        json=json_data,
                    )
                    response.raise_for_status()

                if not force_api_key:
                    api_key_manager.update_index()
                return {"data": response.json(), "used_key": api_key}

            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code

                if status == 400:
                    # Bad Request — parameter tidak valid, langsung raise
                    detail = exc.response.text
                    raise RuntimeError(f"{status} - {detail}") from exc

                elif status == 401:
                    # Unauthorized — API key tidak valid, mark dead, coba key lain
                    logger.error(
                        "[Unauthorized] Key %s invalid (401). Disabling.",
                        api_key[:8],
                    )
                    await api_key_manager.mark_key_dead(api_key)
                    skip_to_next_key = True
                    break

                elif status == 500:
                    # Internal Server Error — coba proxy lain
                    logger.error(
                        "[Server Error] 500 from API with key %s", api_key[:8]
                    )
                    if proxy_url:
                        await proxy_manager.set_cooldown(proxy_url)
                    continue

                elif status == 503:
                    # Service Unavailable — coba proxy lain
                    logger.warning(
                        "[Service Unavailable] 503 from API with key %s",
                        api_key[:8],
                    )
                    if proxy_url:
                        await proxy_manager.set_cooldown(proxy_url)
                    continue

                # Unexpected status code — log dan coba lagi
                logger.warning(
                    "[Unexpected] Status %d from API with key %s",
                    status,
                    api_key[:8],
                )
                if proxy_url:
                    await proxy_manager.set_cooldown(proxy_url)

            except Exception as exc:
                last_error = exc
                if proxy_url:
                    await proxy_manager.set_cooldown(proxy_url)

        if skip_to_next_key:
            continue

        # Try direct (no proxy) as fallback
        try:
            req_headers = dict(headers or {})
            req_headers["x-freepik-api-key"] = api_key
            req_headers.setdefault("Content-Type", "application/json")

            logger.info("[Request] Key %s... Direct", api_key[:8])
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=req_headers,
                    json=json_data,
                )
                response.raise_for_status()

            if not force_api_key:
                api_key_manager.update_index()
            return {"data": response.json(), "used_key": api_key}

        except httpx.HTTPStatusError as exc:
            last_error = exc
            status = exc.response.status_code
            if status == 400:
                raise RuntimeError(f"{status} - {exc.response.text}") from exc
            elif status == 401:
                await api_key_manager.mark_key_dead(api_key)
                continue
        except Exception as exc:
            last_error = exc

    if last_error:
        raise RuntimeError(f"500 - Semua request gagal: {last_error}") from last_error
    raise RuntimeError("500 - Semua request gagal")
