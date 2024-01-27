"""
This module helps to import the correct query module for the Storage-Backend.
"""
from trace_explorer.config import DB_SETTINGS
from . import elasticsearch_helper, jaegery_query_helper

DB_ENGINE = DB_SETTINGS.get('ENGINE')

queries = {
    'Elasticsearch': elasticsearch_helper,
    'JaegerQuery': jaegery_query_helper
}

def get_query():
    """Returns the query module for the specified Storage-Backend (config)."""
    return queries.get(DB_ENGINE)
