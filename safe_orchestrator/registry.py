"""Typed MCP tool registry with signed manifest validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class RiskClass(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class ToolManifest:
    name: str
    version: str
    authority: str
    capabilities: tuple[str, ...]
    risk_class: RiskClass
    description: str
    requires_approval: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolManifest":
        name = data.get("name", "")
        if not re.match(r"^[a-z0-9_:-]{1,64}$", name):
            raise ValueError(f"Invalid tool name: {name!r}")

        authority = data.get("authority", "")
        if not authority or len(authority) > 256:
            raise ValueError("authority must be a non-empty string <= 256 chars")

        description = str(data.get("description", ""))
        # Strip prompt-injection friendly characters and enforce length.
        description = re.sub(r"[<>'\"{}\[\]]", "", description)
        if len(description) > 500:
            raise ValueError("description exceeds 500 chars")

        risk = RiskClass(data.get("risk_class", "low"))
        caps = tuple(str(c) for c in data.get("capabilities", []))

        return cls(
            name=name,
            version=data.get("version", "0.0.0"),
            authority=authority,
            capabilities=caps,
            risk_class=risk,
            description=description,
            requires_approval=bool(
                data.get("requires_approval", risk in (RiskClass.HIGH, RiskClass.CRITICAL))
            ),
            meta=data.get("meta", {}),
        )


ToolHandler = Callable[..., Any]


class ToolRegistry:
    """In-memory registry of validated tools.

    In production, authority fingerprints should be verified against a CDS or
    SPIFFE/SPIRE identity store before registration.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolManifest] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._trusted_authorities: set[str] = set()

    def trust_authority(self, fingerprint: str) -> None:
        self._trusted_authorities.add(fingerprint)

    def untrust_authority(self, fingerprint: str) -> None:
        self._trusted_authorities.discard(fingerprint)

    def register(self, manifest: ToolManifest, handler: ToolHandler) -> None:
        if manifest.authority not in self._trusted_authorities:
            raise PermissionError(
                f"Authority {manifest.authority!r} is not trusted"
            )

        if manifest.name in self._tools:
            existing = self._tools[manifest.name]
            if existing.authority != manifest.authority or existing.version != manifest.version:
                raise RuntimeError(
                    f"Tool shadowing detected for {manifest.name}: "
                    f"existing={existing.authority}@{existing.version}, "
                    f"new={manifest.authority}@{manifest.version}"
                )
            # Idempotent re-registration of identical manifest is allowed.
            return

        # Description poisoning heuristic: a description that contains
        # directive-like instructions is suspicious.
        if re.search(
            r"(ignore previous|disregard|instead (do|run)|override)",
            manifest.description,
            re.IGNORECASE,
        ):
            raise ValueError(
                f"Manifest description for {manifest.name} contains possible prompt-injection patterns"
            )

        self._tools[manifest.name] = manifest
        self._handlers[manifest.name] = handler

    def get(self, name: str) -> tuple[ToolManifest, ToolHandler] | None:
        manifest = self._tools.get(name)
        if manifest is None:
            return None
        return manifest, self._handlers[name]

    def list_tools(self) -> list[ToolManifest]:
        return sorted(self._tools.values(), key=lambda m: m.name)

    def deregister(self, name: str) -> None:
        self._tools.pop(name, None)
        self._handlers.pop(name, None)

    def manifest_json(self) -> str:
        return json.dumps(
            [self._manifest_to_dict(m) for m in self._tools.values()],
            indent=2,
            sort_keys=True,
        )

    @staticmethod
    def _manifest_to_dict(manifest: ToolManifest) -> dict[str, Any]:
        return {
            "name": manifest.name,
            "version": manifest.version,
            "authority": manifest.authority,
            "capabilities": list(manifest.capabilities),
            "risk_class": manifest.risk_class.value,
            "description": manifest.description,
            "requires_approval": manifest.requires_approval,
        }
