from __future__ import annotations

import os


APP_NAME = "TrendsBot"
MODE = os.getenv("TRENDSBOT_MODE", "test").lower()
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "240"))
MAX_SIGNAL_AGE_MINUTES = int(os.getenv("MAX_SIGNAL_AGE_MINUTES", "5"))
MAX_LAUNCHES_PER_CYCLE = int(os.getenv("MAX_LAUNCHES_PER_CYCLE", "2"))

# Hard safety boundaries for the current intelligence-only phase.
TOKEN_LAUNCH_ENABLED = os.getenv("TOKEN_LAUNCH_ENABLED", "false").lower() == "true"
TRADING_ENABLED = False
SELF_BUY_ENABLED = False

if MODE not in {"test", "observation", "production"}:
    raise ValueError("TRENDSBOT_MODE must be test, observation, or production")

if SCAN_INTERVAL_MINUTES < 1:
    raise ValueError("SCAN_INTERVAL_MINUTES must be positive")

if MAX_SIGNAL_AGE_MINUTES < 1:
    raise ValueError("MAX_SIGNAL_AGE_MINUTES must be positive")

if MAX_LAUNCHES_PER_CYCLE < 0:
    raise ValueError("MAX_LAUNCHES_PER_CYCLE cannot be negative")

# Production launch remains impossible until the launch subsystem is explicitly built.
if MODE != "production":
    TOKEN_LAUNCH_ENABLED = False
