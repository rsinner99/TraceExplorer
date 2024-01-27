"""
This module helps to connect to a jaeger query instance specified in the config.
Performs queries and return corresponding output as formatted by the internal 
jaeger query api.
"""
# api/traces?end=1706312483062000&limit=20&lookback=1h&maxDuration&minDuration&service=api&start=1706308883062000

import logging
import requests

from trace_explorer.config import DB_SETTINGS
from trace_explorer.definitions import span

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


BASE_URL = f"http://{DB_SETTINGS.get('URL')}:{DB_SETTINGS.get('PORT')}"

def get_services():
    response = requests.get(
        f"{BASE_URL}/api/services"
    )
    response.raise_for_status()
    return response.json()["data"]


def get_traces(service, start, end):
    params = {
        "start": start,
        "end": end,
        "service": service,
        
    }
    response = requests.get(
        f"{BASE_URL}/api/traces",
        params=params
    )
    response.raise_for_status()
    return response.json()["data"]


def get_spans_in_range(start: int, end: int):
    services = get_services()
    traces = []
    for service in services:
        traces.extend(get_traces(
            service=service,
            start=start,
            end=end
        ))
    unique_traces = {}
    for item in traces:
        print(item)
        unique_traces[item["traceID"]] = item['spans']
    return unique_traces


    