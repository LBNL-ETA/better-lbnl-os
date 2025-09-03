"""Shared types for template readers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from better_lbnl_os.models import BuildingData, UtilityBillData


@dataclass
class ParseMessage:
    severity: str  # 'error' | 'warning'
    message: str
    sheet: Optional[str] = None
    row: Optional[int] = None
    column: Optional[str] = None
    value: Optional[Any] = None
    suggestion: Optional[str] = None


@dataclass
class ParsedPortfolio:
    buildings: List[BuildingData] = field(default_factory=list)
    bills_by_building: Dict[str, List[UtilityBillData]] = field(default_factory=dict)
    errors: List[ParseMessage] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

