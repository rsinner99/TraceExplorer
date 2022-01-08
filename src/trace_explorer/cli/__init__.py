"""
This module provides an entrypoint for command-line based analysis of traces.
"""

import sys
import logging
from trace_explorer.analysis import read_csv_and_analyze

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%m-%d-%Y %H:%M:%S')

def main():
    """Main function for command line."""
    args = sys.argv
    args.pop(0)

    if '-v' in args:
        stdout_handler.setLevel(logging.DEBUG)
    else:
        stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    read_csv_and_analyze()
