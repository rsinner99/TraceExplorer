"""
This module helps to connect to any Elasticsearch instance specified in the config.
Performs queries and return corresponding output as formatted in the ES-Storage-Backend.
"""
import logging

from datetime import datetime
from elasticsearch import Elasticsearch

from trace_explorer.config import DB_SETTINGS
from trace_explorer.definitions import span

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


BASE_URL = f"http://{DB_SETTINGS.get('URL')}:{DB_SETTINGS.get('PORT')}"
es = Elasticsearch(BASE_URL)


def get_span_query(gte: int, lte: int):
    """Return an es-query for all spans in the time range."""
    query = {
        "range": {
            "startTime": {
                "gte": gte,
                "lte": lte
            }
        }
    }
    return query

def get_error_query(gte: int, lte: int):
    """Return an es-query for all spans containing the error tag."""
    query = {
        "bool": {
            "must": [
                {
                    "range": {
                        "startTime": {
                            "gte": gte,
                            "lte": lte
                        }
                    }
                },
                {
                    "nested": {
                        "path": "tags",
                        "score_mode": "avg",
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            "tags.key": "error"
                                        }
                                    },
                                    {
                                        "match": {
                                            "tags.value": True
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            ]
        }
    }
    return query

def get_single_span_query(span_id):
    """Returns an es-query for the given SpanID."""
    query = {
        "bool": {
            "must": [
                {
                    "match": {
                        "spanID": span_id
                    }
                }
            ]
        }
    }
    return query

def remove_elasticsearch_metadata(data):
    """
    Takes data queried from Elasticsearch and removes all unnecessary metadata which where
    produced by Elasticsearch/ Indexing.
    """
    result = []
    for entry in data:
        hits = entry.get('hits')
        if not hits.get('total'):
            return []

        spans = hits.get('hits')
        for span in spans:
            if span.get('_type') not in ['span', '_doc']:
                raise Exception('Dataset is of type: "' + span.get('_type') + '", not "span"')
            source = span.get('_source')
            result.append(source)

    return result

def get_spans_in_range(start: int, end: int):
    """Returns all spans in the specified time range."""
    index = 'jaeger-span-' + datetime.now().strftime('%Y-%m-%d')
    query = get_span_query(start, end)

    # Initialize the scroll
    page = es.search(
        index=index,
        scroll = '2m',
        size = 1000,
        query = query
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']
    if isinstance(scroll_size, dict):
        scroll_size = scroll_size['value']

    result = [page]
    # Start scrolling
    while scroll_size > 0:
        page = es.scroll(scroll_id = sid, scroll = '2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        # Do something with the obtained page
        result.append(page)

    return remove_elasticsearch_metadata(result)

def get_span_from_storage(span_id):
    """
    Returns a single span representation by its SpanID.
    """
    logger.info('Trying to retrieve span-data for unresolved reference: %s', span_id)
    index = 'jaeger-span-' + datetime.now().strftime('%Y-%m-%d')
    query = get_single_span_query(span_id)

    # Initialize the scroll
    page = es.search(
        index=index,
        scroll = '2m',
        size = 1000,
        query = query
    )

    result = [page]
    return remove_elasticsearch_metadata(result)