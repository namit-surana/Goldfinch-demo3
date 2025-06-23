"""
API layer for the TIC Research API
"""

from .server import app
from .endpoints import *

__all__ = [
    'app'
] 