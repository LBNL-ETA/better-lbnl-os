"""Template readers for portfolio input files (BETTER, Portfolio Manager).

Slim, framework-free readers that parse input files into a unified container.
"""

from .types import ParsedPortfolio, ParseMessage
from .better_excel import read_better_excel
from .portfolio_manager import read_portfolio_manager
from .detect import detect_template, read_portfolio

__all__ = [
    "ParsedPortfolio",
    "ParseMessage",
    "read_better_excel",
    "read_portfolio_manager",
    "detect_template",
    "read_portfolio",
]

