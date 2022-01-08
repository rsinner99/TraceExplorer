"""
This module helps to write test results into a temporary csv file,
which will be used for analysis afterwards.
"""

import pandas as pd
from trace_explorer.config import CSV_PATH


def write_result(result):
    """Append test result to csv file."""
    dataframe = pd.DataFrame(result, index=[0])
    csv = dataframe.to_csv(sep=';', index=False, header=False)

    with open(CSV_PATH, 'a', encoding='utf-8') as file:
        # -1: otherwise there will be two linebreaks in the csv per row entries
        file.write(csv)
