"""
This module helps to start the analysis and all corresponding actions.
"""

import logging
import pandas as pd

from trace_explorer.queries import get_query
from trace_explorer.parsers import get_parser
from trace_explorer.reports.html import create_szenario_html, create_trace_html
from trace_explorer.rules.parser import get_rules
from trace_explorer import config

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
        try:
            traces.append(Trace(trace_id, spans))
        except ValueError as ve:
            logger.error('ValueError while analyzing trace %s', trace_id, exc_info=ve)

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


def check_traces_and_exit(szenarios):
    """
    Checks if any trace contains an error.
    Exit with status code 1 if an error was found.
    Otherwise exit with status code 0.
    """
    try:
        next(True for szen in szenarios if szen.traces_error_count)
        logger.info('Detected at least one error in the traces.')
        exit(1)
    except StopIteration:
        logger.info('No errors detected in the traces.')
        exit(0)


def read_csv_and_analyze():
    """Helper function to read csv and trigger analysis."""
    logger.debug("Reading szenario information from csv.")
    szenarios = []
    rules = get_rules()
    dataframe = pd.read_csv(config.CSV_PATH, sep=';')
    for data in dataframe.values.tolist():
        szenarios.append(analyze_traces(data[0], data[1], data[2], data[3], data[4], rules))
    create_szenario_html(szenarios)

    check_traces_and_exit(szenarios)


def analyze_custom_time_range(start_time, end_time, name):
    """Helper function to use custom start and end time to trigger analysis."""
    logger.debug("Reading szenario information from command line.")
    rules = get_rules()
    szenarios = [analyze_traces(start_time, end_time, name, "", "", rules)]
    create_szenario_html(szenarios)
    check_traces_and_exit(szenarios)
