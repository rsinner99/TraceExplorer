"""
This module provides general configuration parameters for the analysis.
It's recommended to set these parameters via environment variables.
"""
import os

root = os.path.dirname(os.path.abspath(__file__))
cwd = os.getcwd()

DB_SETTINGS = {
    "ENGINE": os.environ.get('RCA_DB_ENGINE', 'Elasticsearch'),
    "URL": os.environ.get('RCA_DB_URL', '127.0.0.1'),
    "PORT": os.environ.get('RCA_DB_PORT', '9200'),
    "DATAFORMAT": os.environ.get('RCA_DB_DATAFORMAT', 'OpenTracing')
}

JSON_SCHEMA_PATH = os.path.join(root, os.environ.get('RCA_SCHEMA_PATH', 'schemas/schema.json'))

RULE_BASE_DIR = os.path.join(root, os.environ.get('RCA_RULE_DIR', 'rules/rules'))

CSV_PATH = os.path.join(cwd, os.environ.get('RCA_CSV_PATH', ''))

REPORT_DIR = os.path.join(cwd, os.environ.get('RCA_REPORT_DIR', ''))
