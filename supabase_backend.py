"""Small Supabase REST adapter used by the Streamlit research desk.

It deliberately uses the browser-safe publishable key plus the signed-in
user's access token.  The service-role key is never required by the app.
"""
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


def _setting(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, "")).strip()


def configured() -> bool:
    return bool(_setting("SUPABASE_URL") and _setting("SUPABASE_ANON_KEY"))


def _base() -> str:
    return _setting("SUPABASE_URL").rstrip("/")


def _headers(token: str | None = None, *, prefer: str | None = None) -> dict[str, str]:
    key = _setting("SUPABASE_ANON_KEY")
    headers = {"apikey": key, "Authorization": f"Bearer {token or key}", "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _error(response: requests.Response) -> str:
    try:
        payload = response.json()
        return str(payload.get("msg") or payload.get("message") or payload.get("error_description") or payload)
    except Exception:
        return response.text or f"HTTP {response.status_code}"


def sign_up(email: str, password: str) -> tuple[dict[str, Any] | None, str | None]:
    response = requests.post(
        f"{_base()}/auth/v1/signup", headers=_headers(), json={"email": email.strip(), "password": password}, timeout=15
    )
    if not response.ok:
        return None, _error(response)
    data = response.json()
    user = data.get("user") or {}
    token = data.get("access_token")
    if not token:
        return None, "注册邮件已发出，请先完成邮箱验证后再登录。"
    return {"id": user.get("id"), "username": user.get("email"), "email": user.get("email"), "access_token": token}, None


def sign_in(email: str, password: str) -> tuple[dict[str, Any] | None, str | None]:
    response = requests.post(
        f"{_base()}/auth/v1/token?grant_type=password", headers=_headers(), json={"email": email.strip(), "password": password}, timeout=15
    )
    if not response.ok:
        return None, _error(response)
    data = response.json()
    user = data.get("user") or {}
    return {"id": user.get("id"), "username": user.get("email"), "email": user.get("email"), "access_token": data.get("access_token")}, None


def _rest(method: str, table: str, auth_user: dict[str, Any], *, params: dict[str, str] | None = None, data: Any = None, prefer: str | None = None) -> requests.Response:
    return requests.request(method, f"{_base()}/rest/v1/{table}", headers=_headers(auth_user["access_token"], prefer=prefer), params=params, json=data, timeout=15)


def list_screens(auth_user: dict[str, Any]) -> list[dict[str, Any]]:
    response = _rest("GET", "saved_screens", auth_user, params={"select": "id,name,payload,updated_at", "order": "updated_at.desc"})
    response.raise_for_status()
    return response.json()


def upsert_screen(auth_user: dict[str, Any], name: str, payload: dict[str, Any]) -> bool:
    response = _rest("POST", "saved_screens", auth_user, data={"user_id": auth_user["id"], "name": name, "payload": payload}, prefer="resolution=merge-duplicates,return=representation")
    response.raise_for_status()
    return True


def remove_screen(auth_user: dict[str, Any], screen_id: str) -> None:
    response = _rest("DELETE", "saved_screens", auth_user, params={"id": f"eq.{screen_id}"})
    response.raise_for_status()


def list_watchlist(auth_user: dict[str, Any]) -> list[str]:
    response = _rest("GET", "watchlist", auth_user, params={"select": "bond_code", "order": "added_at.desc"})
    response.raise_for_status()
    return [item["bond_code"] for item in response.json()]


def add_to_watchlist(auth_user: dict[str, Any], codes: list[str]) -> None:
    if not codes:
        return
    rows = [{"user_id": auth_user["id"], "bond_code": code} for code in codes]
    response = _rest("POST", "watchlist", auth_user, data=rows, prefer="resolution=ignore-duplicates")
    response.raise_for_status()


def remove_from_watchlist(auth_user: dict[str, Any], codes: list[str]) -> None:
    for code in codes:
        response = _rest("DELETE", "watchlist", auth_user, params={"bond_code": f"eq.{code}"})
        response.raise_for_status()
