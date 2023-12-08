"""
This module implements the actual root cause analysis of the tracing data.
"""

import logging

from trace_explorer.config import MAX_CLOCK_DEVIATION

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def compare_log_timestamps(span_a, span_b):
    """
    Calculates the diff between two timestamps.
    If the diff is below a user defined limit,
    the cause of the failure cannot be determined.
    Both spans get rated the same if that happens.
    """
    diff = abs(span_a.cause_timestamp - span_b.cause_timestamp)
    if diff < MAX_CLOCK_DEVIATION:
        logger.warning(f'Error interval of {diff} microseconds is below user defined limit of {MAX_CLOCK_DEVIATION} microseconds. No reliable analysis possible for those errors."')
        sum = span_a.rating + span_b.rating
        span_a.rating = sum / 2
        span_b.rating = sum / 2


def resolve_cause_relation(span_caused, span_effected):
    """Sets pointers for caused and caused_by references."""
    tmp = span_effected.caused_by
    span_caused.caused = span_effected
    span_effected.caused_by = span_caused
    if tmp:
        tmp.caused = span_caused
        span_caused.caused_by = tmp

def rating_hierarchy_level(span):
    """Rates the errors in one hierarchy level."""
    for child in span.children:
        if child.previous:
            if child.error and child.previous.error:
                if child.start_time > child.previous.end_time:
                    resolve_cause_relation(child.previous, child)
                    child.previous.rating += 1
                    # if timestamps are too close, both spans get rated the same
                    compare_log_timestamps(child.previous, child)

def get_root_cause(parent):
    """Recursive function for rating the errors in a hierachical span structure."""
    parent_rating = 0
    if parent.has_children():
        rating_hierarchy_level(parent)
        for child in parent.children:
            if child.error and parent.error:
                if child.type == 'child':
                    logger.debug('Child_of: child.error and parent.error')
                    earlier = sorted([child, parent], key=lambda span: span.cause_timestamp)
                    logger.debug('earlier (+1) - %s', earlier[0].span_id)
                    resolve_cause_relation(earlier[0], earlier[1])
                    earlier[0].rating += 1 + earlier[1].rating
                if child.type == 'follower':
                    logger.debug('Follows_from: child.error and parent.error')
                    if parent.cause_timestamp < child.cause_timestamp:
                        logger.debug('Only parent (+1) - %s', parent.span_id)
                        resolve_cause_relation(parent, child)
                        parent.rating += 1
                    else:
                        logger.debug('Both (+1) - %s & %s', parent.span_id, child.span_id)
                        child.rating += 1
                        parent.rating += 1
                # if timestamps are too close, both spans get rated higher
                compare_log_timestamps(child, parent)

            elif child.error:
                logger.debug('Only child (+1) - %s', child.span_id)
                child.rating +=1
            elif parent.error:
                logger.debug('Only parent (+1) - %s', parent.span_id)
                parent_rating += 1

            get_root_cause(child)
        # number of children should not influence the value of parent rating
        parent.rating += parent_rating / len(parent.children)
