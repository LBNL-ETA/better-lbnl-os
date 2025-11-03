"""Auto-detection and convenience wrapper for template readers."""

from __future__ import annotations

import pandas as pd

from .better_excel import read_better_excel
from .portfolio_manager import read_portfolio_manager
from .types import ParsedPortfolio


def detect_template(file_like) -> str | None:
    """Detect template type by looking for known sheet names.

    Returns 'better_excel' | 'portfolio_manager' | None
    """
    try:
        xl = pd.ExcelFile(file_like)
        sheets = set(xl.sheet_names)
    except Exception:
        return None

    if {"Property Information", "Utility Data"}.issubset(sheets):
        return "better_excel"
    if {"Properties", "Meter Entries"}.issubset(sheets):
        return "portfolio_manager"
    return None


def read_portfolio(file_like, template_type: str = "auto") -> ParsedPortfolio:
    """High-level helper to read either template type.

    template_type: 'auto' | 'better_excel' | 'portfolio_manager'
    """
    ttype = template_type
    if template_type == "auto":
        ttype = detect_template(file_like) or "better_excel"
    if ttype == "portfolio_manager":
        return read_portfolio_manager(file_like)
    return read_better_excel(file_like)
