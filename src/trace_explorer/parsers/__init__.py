"""
This module helps to import the correct parser
for the specified format in the config.
"""
from trace_explorer.config import DB_SETTINGS
from . import opentracing

DB_DATAFORMAT = DB_SETTINGS.get('DATAFORMAT', 'OpenTracing')

parsers = {
    'OpenTracing': opentracing
}

def get_parser():
    """Return the parser for the specified dataformat (config)."""
    return parsers.get(DB_DATAFORMAT)
