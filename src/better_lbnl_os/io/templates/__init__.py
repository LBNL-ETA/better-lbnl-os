"""Template readers for portfolio input files (BETTER, Portfolio Manager).

Slim, framework-free readers that parse input files into a unified container.
"""

from .better_excel import read_better_excel
from .detect import detect_template, read_portfolio
from .portfolio_manager import read_portfolio_manager
from .types import ParsedPortfolio, ParseMessage

__all__ = [
    "ParseMessage",
    "ParsedPortfolio",
    "detect_template",
    "read_better_excel",
    "read_portfolio",
    "read_portfolio_manager",
]
