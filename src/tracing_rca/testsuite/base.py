"""This module implements a base class to inherit from in test cases."""
import time
import math
import logging
import unittest

from .csv import write_result

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Runner(unittest.TestCase):
    """This class implements a base the case to inherit from."""

    def run(self, result=None):
        """Overrides the run function to retrive start and end time."""
        # Get start time of the test
        start_time = math.floor(time.time_ns() / 1e3) # microseconds: rounded down
        logger.debug('Start: %r', start_time)
        time.sleep(1)

        # Perform actual test
        super().run(result)

        # Get end time of test
        time.sleep(1)
        end_time = math.ceil(time.time_ns() / 1e3) # microseconds: rounded up
        logger.debug('End: %r', end_time)

        # Write results to temporary csv
        params = {
            'start_time': start_time,
            'end_time': end_time,
            'name': self.__class__.__name__,
            'errors': str(result.errors),
            'failures': str(result.failures)
        }
        write_result(params)
