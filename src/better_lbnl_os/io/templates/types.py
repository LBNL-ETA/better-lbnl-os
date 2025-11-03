"""Shared types for template readers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from better_lbnl_os.models import BuildingData, UtilityBillData


@dataclass
class ParseMessage:
    """Message from template parsing (error or warning)."""

    severity: str  # 'error' | 'warning'
    message: str
    sheet: str | None = None
    row: int | None = None
    column: str | None = None
    value: Any | None = None
    suggestion: str | None = None


@dataclass
class ParsedPortfolio:
    """Result of parsing a portfolio template."""

    buildings: list[BuildingData] = field(default_factory=list)
    bills_by_building: dict[str, list[UtilityBillData]] = field(default_factory=dict)
    errors: list[ParseMessage] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
