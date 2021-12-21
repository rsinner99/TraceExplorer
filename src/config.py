"""
This module provides general configuration parameters for the analysis.
It's recommended to set these parameters via environment variables.
"""
import os

DB_SETTINGS = {
    "ENGINE": os.environ.get('RCA_DB_ENGINE'),
    "URL": os.environ.get('RCA_DB_URL'),
    "PORT": os.environ.get('RCA_DB_PORT'),
    "DATAFORMAT": os.environ.get('RCA_DB_DATAFORMAT')
}

JSON_SCHEMA_PATH = os.environ.get('RCA_SCHEMA_PATH')

RULE_BASE_DIR = os.environ.get('RCA_RULE_DIR')

CSV_PATH = os.environ.get('RCA_CSV_PATH')

REPORT_DIR = os.environ.get('RCA_REPORT_DIR')
