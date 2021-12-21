"""
This module helps to connect to any Elasticsearch instance specified in the config.
Performs queries and return corresponding output as formatted in the ES-Storage-Backend.
"""

from datetime import datetime
from elasticsearch import Elasticsearch

from config import DB_SETTINGS

es = Elasticsearch(
    [DB_SETTINGS.get('URL')],
    scheme="http",
    port=DB_SETTINGS.get('PORT'),
)

BASE_URL = 'http://' + DB_SETTINGS.get('URL') + ':' + DB_SETTINGS.get('PORT') + '/'
SEARCH_URL = "_search?pretty"
HEADERS = {
    "Content-Type": "application/json"
}

def get_span_query(gte: int, lte: int):
    """Return a es-query for all spans in the time range."""
    query = {
        "query": {
            "range": {
                "startTime": {
                    "gte": gte,
                    "lte": lte
                }
            }
        }
    }
    return query

def get_error_query(gte: int, lte: int):
    """Return a es-query for all spans containing the error tag."""
    query = {
        "query": {
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
            if span.get('_type') != 'span':
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
        body = query
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']

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
