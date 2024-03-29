"""
This module provides an entrypoint for command-line based analysis of traces.
"""

import re
import sys
import logging
import math
import time
from datetime import timedelta
from argparse import ArgumentParser
from tracemalloc import start
from trace_explorer.analysis import read_csv_and_analyze, analyze_custom_time_range

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%m-%d-%Y %H:%M:%S')


def prepare_args():
    parser = ArgumentParser(
                    prog = 'TraceExplorer',
                    description = 'Analyze recorded traces to identify the root cause of an error.',
                    epilog = '')

    parser.add_argument('-s', '--start',
                        help='Start time for interval to check in the past. E.g. 10s / 5m / 1h')
    parser.add_argument('-e', '--end',
                        help='''Start time for interval to check in the past. E.g. 10s / 5m / 1h.
                        If not set, current time is used as end.''')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose logging.')
    
    return parser


def get_timedelta(value):
    kwargs = {}
    m = re.match(r'(\d+)(s|m|h)', value)
    if not m:
        logger.error(f"Invalid format for time: '{value}'")
        sys.exit(-1)
    unit = m.group(2)
    value = int(m.group(1))
    if unit == 's':
        kwargs['seconds'] = value
    elif unit == 'm':
        kwargs['minutes'] = value
    elif unit == 'h':
        kwargs['hours'] = value
    return timedelta(**kwargs).total_seconds() * 1e6 # microseconds


def main():
    """Main function for command line."""
    parser = prepare_args()
    args = parser.parse_args()

    if args.verbose:
        stdout_handler.setLevel(logging.DEBUG)
    else:
        stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    if args.start:
        current = math.ceil(time.time_ns() / 1e3) # microseconds: rounded up
        start_delta = get_timedelta(args.start)
        start_time = current - start_delta
        if args.end:
            end_delta = get_timedelta(args.end)
            end_time = current - end_delta
        else:
            end_time = current

        name = f"CustomSzenario - {current}"
        analyze_custom_time_range(start_time, end_time, name)

    read_csv_and_analyze()
