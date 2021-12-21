"""
This module provides an entrypoint for command-line based analysis of traces.
"""

import sys
import logging
from tracing_rca.analysis import read_csv_and_analyze

def main():
    args = sys.argv
    args.pop(0)
    print(args)
    if '-v' in args:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    read_csv_and_analyze()