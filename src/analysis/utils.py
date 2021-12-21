"""
This module helps to start the analysis and all corresponding actions.
"""

import os
import logging
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from .models import Trace, Szenario
from .rca import get_root_cause
from ..queries import get_query
from ..parsers import get_parser
from ..reports.html import html_graph
from ..rules.parser import get_rules


logger = logging.getLogger("analysis.utils")
logger.setLevel(logging.DEBUG)

root = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(root, 'templates')
env = Environment( loader = FileSystemLoader(templates_dir) )


def create_trace_html(traces):
    """Creates a HTML report for each Trace in the list."""
    for trace in traces:
        if trace.error_count == 0:
            continue
        spans = sorted(trace.spans, key=lambda span: span.rating, reverse=True)
        spans = [span.__dict__() for span in spans if span.error]
        graph = html_graph(trace.root_span)
        template = env.get_template('spans.html')
        output = template.render(spans=spans, trace=trace.__dict__(), graph=graph)
        with open(trace.filename, 'w', encoding='utf-8') as file:
            file.write(output)

def create_szenario_html(szenarios):
    """Creates a file with szenarios details."""
    result = [szenario.__dict__() for szenario in szenarios]
    filename = 'szenario_test.html'
    template = env.get_template('szenarios.html')
    output = template.render(szenarios=result)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(output)

def analyze_traces(start_time, end_time, name, errors, failures, rules):
    """Initailizes the analysis."""
    query = get_query()
    parser = get_parser()
    data = query.get_spans_in_range(start_time, end_time)

    traces_raw = parser.parse_spans(data)

    logger.debug('Trace IDs: %r', list(traces_raw.keys()))
    traces = []

    for trace_id, spans in traces_raw.items():
        traces.append(Trace(trace_id, spans))

    szenario = Szenario(name, errors, failures)

    for trace in traces:
        get_root_cause(trace.root_span)

        for span in trace.spans:
            for rule in rules:
                rule.perform(span)

        szenario.add_trace(trace)

    create_trace_html(traces)
    return szenario



def read_csv_and_analyze():
    szenarios = []
    rules = get_rules()
    df = pd.read_csv("test_results.csv", sep=';')
    for data in df.values.tolist():
        szenarios.append(analyze_traces(data[0], data[1], data[2], data[3], data[4], rules))
    create_szenario_html(szenarios)
