"""Bind to the container interface; the host publication stays loopback-only."""
import os

port = int(os.environ.get("APP_PORT", "8001"))
if port not in (8001, 8002, 8003, 8004):
    raise ValueError("APP_PORT must match one of the four KR2 variants")
bind = f"0.0.0.0:{port}"
workers = 2
accesslog = "-"
errorlog = "-"
timeout = 30
