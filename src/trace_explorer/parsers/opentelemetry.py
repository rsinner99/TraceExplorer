"""
This module implements a parser for the opentracing format.
"""

import json
from jsonschema import validate as validate_json

from trace_explorer.config import JSON_SCHEMA_PATH
from trace_explorer.definitions import logs, span as span_def

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

def extract_error_logs_from_tags(span_data):
    log_data = []
    log_fields = {}
    tags = span_data[span_def.TAGS]
    if tags.get('otel.status_code'):
        log_fields[logs.FIELD_EVENT] = tags['otel.status_code'].lower()
    if tags.get('otel.status_description'):
        log_fields[logs.FIELD_STACK] = tags['otel.status_description']
        # last line of stacktrace is the exception
        log_fields[logs.FIELD_MESSAGE] = log_fields[logs.FIELD_STACK][-1]
    if log_fields:
        log_data.append({
            logs.FIELDS: log_fields,
            # set timestamp to end of trace, because we don´t know anything better
            logs.TIMESTAMP: span_data[span_def.START_TIME] + span_data[span_def.DURATION]
        })
    return log_data

def validate(span_data):
    """Validates a span representation with a given JSON-Schema"""
    with open(JSON_SCHEMA_PATH, 'r', encoding="utf-8") as file:
        schema = file.read()
    validate_json(instance=span_data, schema=json.loads(schema))

def extract_span_data(data):
    """Extractes all relevant span data and formats it."""
    result = dict((k, data[k]) for k in RELEVANT_KEYS)
    #if 'process' not in data.keys():
    #    process = data['processes'].keys()[0]
    #    result['service'] = [data['process'][process]['serviceName']] # jaeger query
    #else:
    result['service'] = get_key_value_from_tags(data.get('process', {}).get('tags', [])) #es
    result['tags'] = get_key_value_from_tags(data.get('tags', []))
    if not "process" in data.keys():
        result['service']['name'] = data.get('process', {}).get('serviceName', "unknown")
    else:
        result['service']['name'] = data.get('processes', {}).get('serviceName', "unknown")
    error = result['tags'].get('error', False)
    if isinstance(error, str):
        error = json.loads(error.lower())
    result['tags']['error'] = error
    result['logs'] = get_list_of_logs(data.get('logs'))
    if error and not result['logs']:
        # check if we can get error information from somewhere else
        result['logs'] = extract_error_logs_from_tags(result)
    validate(result)
    return result

def parse_spans(spans):
    """Parsers a list of spans and transforms them into the excpeted format."""
    result = {}
    print(spans)
    for traceID, span_list in spans.items():
        if traceID not in result.keys():
            result[traceID] = {}
        for span in span_list:
            span_id = span.pop('spanID')
            result[traceID][span_id] = extract_span_data(span)
    return result
