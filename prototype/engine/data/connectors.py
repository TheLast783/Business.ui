"""Optional real-data connector layer.

No credentials or vendor lock-in are required for the prototype. A JSON REST endpoint
can be configured with DATA_SOURCE_URL; synthetic scenarios remain the deterministic
fallback used for judging/reproducibility.
"""
import json
import os
import time
import urllib.request
from typing import Any, Dict, Optional


class RESTDataConnector:
    """Small dependency-free JSON connector with timeout and audit metadata."""

    def __init__(self, name: str, url: Optional[str] = None, timeout_s: float = 5.0):
        self.name = name
        self.url = url or os.getenv(f"{name.upper().replace(' ', '_')}_URL")
        self.timeout_s = timeout_s

    def fetch(self) -> Dict[str, Any]:
        if not self.url:
            return {
                "status": "NOT_CONFIGURED",
                "source": self.name,
                "message": "No endpoint configured; synthetic deterministic feed remains active.",
            }
        started = time.time()
        req = urllib.request.Request(self.url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {
                "status": "OK", "source": self.name, "latency_ms": round((time.time()-started)*1000, 1),
                "records": len(payload) if isinstance(payload, list) else 1, "payload": payload,
            }
        except Exception as exc:
            return {
                "status": "ERROR", "source": self.name,
                "latency_ms": round((time.time()-started)*1000, 1),
                "message": str(exc),
            }


class DataConnectorRegistry:
    """Registry for ERP/Web/Jira/external-event connectors."""
    def __init__(self):
        self.connectors = [
            RESTDataConnector("ERP API"),
            RESTDataConnector("Web Analytics API"),
            RESTDataConnector("Jira API"),
            RESTDataConnector("External Events API"),
        ]

    def status(self) -> list:
        return [{
            "connector": c.name,
            "configured": bool(c.url),
            "mode": "LIVE API" if c.url else "SYNTHETIC FALLBACK",
        } for c in self.connectors]
