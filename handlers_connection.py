"""Connection management for Adobe Acrobat Sign Connector."""
from __future__ import annotations
import uuid, json
from typing import Any
from imperal_sdk import ActionResult
from app import chat
from schemas import (
    NoParams, ConnectParams, ConnectionIdParams, ConnectionRecord, ConnectionList, DeleteResult
)
from adobe_acrobat_sign_client import AdobeAcrobatSignClient

_SECRET = "adobe_acrobat_sign_connections"

def _mask(v: str) -> str:
    return v[:4] + "…" + v[-4:] if len(v) > 8 else "***"

async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET)
    if not raw: return []
    try: data = json.loads(raw)
    except: return []
    return data if isinstance(data, list) else []

async def _save_connections(ctx, conns: list[dict]) -> None:
    await ctx.secrets.set(_SECRET, json.dumps(conns))

async def resolve_client(ctx, connection_id: str = "") -> AdobeAcrobatSignClient:
    conns = await _load_connections(ctx)
    if not conns:
        raise ValueError("No Adobe Acrobat Sign connections configured. Use connect_adobe_acrobat_sign first.")
    conn = None
    if connection_id:
        for c in conns:
            if c.get("id") == connection_id:
                conn = c
                break
        if not conn:
            raise ValueError(f"Connection {connection_id} not found.")
    else:
        for c in conns:
            if c.get("is_active"):
                conn = c
                break
        if not conn:
            conn = conns[0]
    return AdobeAcrobatSignClient(access_token=conn["access_token"], base_url=conn.get("base_url", ""))

@chat.function(
    "connect_adobe_acrobat_sign",
    "Connect Adobe Acrobat Sign account via credentials.",
    action_type="write",
    chain_callable=True,
    event="adobe-acrobat-sign-connector.connect_adobe_acrobat_sign",
    effects=["create:connection"],
    data_model=ConnectionRecord
)
async def connect_adobe_acrobat_sign(params: ConnectParams, ctx) -> ActionResult[ConnectionRecord]:
    client = AdobeAcrobatSignClient(access_token=params.access_token, base_url=params.base_url)
    res = await client.verify_auth()
    if res.get("status") == "error":
        return ActionResult.error(f"Failed to authenticate with Adobe Acrobat Sign: {res.get('error')}")

    conns = await _load_connections(ctx)
    cid = f"conn_{uuid.uuid4().hex[:8]}"
    record = {
        "id": cid,
        "label": params.label or "Primary Adobe Acrobat Sign",
        "access_token": params.access_token,
        "masked_key": _mask(params.access_token),
        "base_url": params.base_url,
        "is_active": True
    }
    for c in conns:
        c["is_active"] = False
    conns.append(record)
    await _save_connections(ctx, conns)
    return ActionResult.ok(ConnectionRecord(**record), summary=f"Connected to Adobe Acrobat Sign ({record['label']}).")

@chat.function(
    "list_connections",
    "List configured Adobe Acrobat Sign connections.",
    action_type="read",
    chain_callable=True,
    event="adobe-acrobat-sign-connector.list_connections",
    effects=["read:connections"],
    data_model=ConnectionList
)
async def list_connections(params: NoParams, ctx) -> ActionResult[ConnectionList]:
    conns = await _load_connections(ctx)
    recs = [ConnectionRecord(**c) for c in conns]
    return ActionResult.ok(ConnectionList(connections=recs, total=len(recs)), summary=f"Found {len(recs)} Adobe Acrobat Sign connection(s).")

@chat.function(
    "disconnect_adobe_acrobat_sign",
    "Disconnect Adobe Acrobat Sign account and delete stored credentials.",
    action_type="destructive",
    chain_callable=True,
    event="adobe-acrobat-sign-connector.disconnect_adobe_acrobat_sign",
    effects=["delete:connection"],
    data_model=DeleteResult
)
async def disconnect_adobe_acrobat_sign(params: ConnectionIdParams, ctx) -> ActionResult[DeleteResult]:
    conns = await _load_connections(ctx)
    if not conns:
        return ActionResult.ok(DeleteResult(success=True, message="No active connections to disconnect."), summary="Nothing to disconnect.")
    if params.connection_id:
        conns = [c for c in conns if c.get("id") != params.connection_id]
    else:
        conns = []
    await _save_connections(ctx, conns)
    return ActionResult.ok(DeleteResult(success=True, message="Disconnected Adobe Acrobat Sign."), summary="Disconnected connection.")
