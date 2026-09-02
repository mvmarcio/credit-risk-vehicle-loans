"""Credit risk vehicle loans analysis package."""

from src.extraction import DataExtractor
from src.database import DatabaseManager
from src.analysis import DefaultAnalyzer

# Optional: FipeZAP data module (if available)
try:
    from src.fipezap_data import get_fipezap_data, get_fipezap_summary
    __all__ = [
        'DataExtractor', 
        'DatabaseManager', 
        'DefaultAnalyzer',
        'get_fipezap_data',
        'get_fipezap_summary'
    ]
except ImportError:
    # If fipezap_data.py doesn't exist, still export the main modules
    __all__ = [
        'DataExtractor', 
        'DatabaseManager', 
        'DefaultAnalyzer'
    ]

__version__ = '1.0.0'