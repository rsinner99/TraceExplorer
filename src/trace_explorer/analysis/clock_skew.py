"""This module provides functionality for clock skew adjustment."""
import logging
from trace_explorer.definitions import logs

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_time_shift(parent_time, child_time):
    """
    Calculates the time difference and adds 1.
    Returns the necessary time shift in microseconds.
    """
    diff = parent_time - child_time
    return diff + 1

def adjust_timestamps(span, shift):
    """
    Adds the time shift to all timestamps of the span.
    """
    span.start_time += shift
    span.end_time += shift
    if span.cause_timestamp:
        span.cause_timestamp += shift
    for log in span.logs:
        log[logs.TIMESTAMP] += shift

def adjust_clock_skew(parent, child):
    """
    Adjust timestamp of child if clock skew detected.
    """
    if parent.start_time < child.start_time:
        return

    shift = get_time_shift(parent.start_time, child.start_time)
    adjust_timestamps(child)
    logger.info(
        'Timestamp adjusted in Trace %s: Service "%s" with Span ID "%s"', 
        child.trace_id, child.service, child.span_id
    )
