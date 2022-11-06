"""
This module implements a parser for the opentracing format.
"""

import json
from jsonschema import validate as validate_json

from trace_explorer.config import JSON_SCHEMA_PATH
from trace_explorer.definitions import logs

RELEVANT_KEYS = ['operationName', 'references', 'startTime', 'duration', ]

key_mapping = {
    "exception.message": logs.FIELD_MESSAGE,
    "exception.stacktrace": logs.FIELD_STACK,
    "exception.type": logs.FIELD_ERROR_OBJECT
}

def get_key_value_from_tags(tags):
    """Transforms a list to a key-value-dictionary."""
    kv = []
    for tag in tags:
        if tag.get('key') in key_mapping.keys():
            tag['key'] = key_mapping[tag['key']]
            kv.append(("event", "error"))
        kv.append((tag.get('key'), tag.get('value')))
    return dict(kv)

def get_list_of_logs(logs):
    "Returns a formatted list of all logs of a span."
    result = []
    for log in logs:
        result.append({
            'timestamp': log.get('timestamp'),
            'fields': get_key_value_from_tags(log.get('fields'))
        })
    return result

def validate(span_data):
    """Validates a span representation with a given JSON-Schema"""
    with open(JSON_SCHEMA_PATH, 'r', encoding="utf-8") as file:
        schema = file.read()
    validate_json(instance=span_data, schema=json.loads(schema))

def extract_span_data(data):
    """Extractes all relevant span data and formats it."""
    result = dict((k, data[k]) for k in RELEVANT_KEYS)
    result['service'] = get_key_value_from_tags(data.get('process').get('tags'))
    result['service']['name'] = data.get('process').get('serviceName')
    result['tags'] = get_key_value_from_tags(data.get('tags'))
    error = result['tags'].get('error', False)
    if isinstance(error, str):
        error = json.loads(error.lower())
    result['tags']['error'] = error
    result['logs'] = get_list_of_logs(data.get('logs'))
    validate(result)
    return result

def parse_spans(spans):
    """Parsers a list of spans and transforms them into the excpeted format."""
    result = {}
    for span in spans:
        if not span.get('traceID') in result:
            result[span.get('traceID')] = {}
        span_id = span.pop('spanID')
        result[span.get('traceID')][span_id] = extract_span_data(span)
    return result
