"""
This module helps to import the correct parser
for the specified format in the config.
"""
from trace_explorer.config import DB_SETTINGS
from . import opentracing, opentelemetry

DB_DATAFORMAT = DB_SETTINGS.get('DATAFORMAT', 'OpenTracing')

parsers = {
    'OpenTracing': opentracing,
    'OpenTelemetry': opentelemetry
}

def get_parser():
    """Return the parser for the specified dataformat (config)."""
    return parsers.get(DB_DATAFORMAT)
