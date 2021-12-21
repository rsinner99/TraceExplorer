"""
This module provides an entrypoint for command-line based analysis of traces.
"""

from tracing_rca.analysis import read_csv_and_analyze

def main():
    read_csv_and_analyze()