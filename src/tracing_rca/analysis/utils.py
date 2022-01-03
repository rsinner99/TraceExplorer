"""
This module helps to start the analysis and all corresponding actions.
"""

import logging
import pandas as pd

from tracing_rca.queries import get_query
from tracing_rca.parsers import get_parser
from tracing_rca.reports.html import create_szenario_html, create_trace_html
from tracing_rca.rules.parser import get_rules
from tracing_rca import config

from .models import Trace, Szenario
from .rca import get_root_cause



logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



def analyze_traces(start_time, end_time, name, errors, failures, rules):
    """Initailizes the analysis."""
    query = get_query()
    parser = get_parser()
    data = query.get_spans_in_range(start_time, end_time)

    traces_raw = parser.parse_spans(data)

    logger.info('Trace IDs: %r', list(traces_raw.keys()))
    traces = []

    for trace_id, spans in traces_raw.items():
        traces.append(Trace(trace_id, spans))

    szenario = Szenario(name, errors, failures)

    for trace in traces:
        for span in trace.spans:
            for rule in rules:
                rule.perform(span)
            
        trace.set_error_count()

        get_root_cause(trace.root_span)

        szenario.add_trace(trace)

    create_trace_html(traces)
    return szenario



def read_csv_and_analyze():
    """Helper function to read csv and trigger analysis."""
    szenarios = []
    rules = get_rules()
    dataframe = pd.read_csv(config.CSV_PATH, sep=';')
    for data in dataframe.values.tolist():
        szenarios.append(analyze_traces(data[0], data[1], data[2], data[3], data[4], rules))
    create_szenario_html(szenarios)
