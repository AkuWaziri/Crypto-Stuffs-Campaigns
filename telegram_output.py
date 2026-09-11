"""Telegram output for read-only intelligence observations."""
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from live_observation import Observation

def format_observation(obs: Observation, rank: int) -> str:
    icon={"RESEARCH NOW":"🟢","WATCH":"🟡","PASS":"🔴","INSUFFICIENT DATA":"⚠️","HARD RISK":"🚨"}.get(obs.label,"⚪")
    lines=[f"{icon} #{rank} {obs.symbol or 'UNKNOWN'} · {obs.score}/100", "────────────────────", f"📊 {obs.label}", f"💧 Liquidity: ${obs.liquidity_usd:,.0f}", f"💰 Market Cap: ${obs.market_cap_usd:,.0f}", f"⛓ DEX: {obs.dex}"]
    if obs.hard_risks: lines.append("🚨 Risks: " + ", ".join(obs.hard_risks[:3]))
    if obs.warnings: lines.append("⚠️ Warnings: " + ", ".join(obs.warnings[:4]))
    if obs.signals: lines.append("🔎 Signals: " + ", ".join(obs.signals[:4]))
    lines += [f"🧾 CA: {obs.contract}", f"🔗 {obs.explorer_url}"]
    return "\n".join(lines)

def format_feed(observations: list[Observation]) -> str:
    lines=["🧠 EVM INTELLIGENCE", "READ-ONLY · MANUAL DECISION SUPPORT", "", f"Candidates analyzed: {len(observations)}", ""]
    for index, obs in enumerate(observations, 1): lines.append(format_observation(obs, index)); lines.append("")
    lines.append("No trades or transactions are executed by this system.")
    return "\n".join(lines)

def send_telegram(text: str, token: str | None = None, chat_id: str | None = None) -> None:
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: raise RuntimeError("Telegram configuration is missing")
    url=f"https://api.telegram.org/bot{token}/sendMessage"
    body=urllib.parse.urlencode({"chat_id":chat_id,"text":text}).encode()
    request=urllib.request.Request(url,data=body,headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
    with urllib.request.urlopen(request,timeout=15) as response:
        payload=json.loads(response.read().decode())
    if not isinstance(payload,dict) or payload.get("ok") is not True: raise RuntimeError("Telegram send failed")
