import os
import unittest
import json

from tracing_rca.parsers import get_parser
from tracing_rca.analysis.models import Trace
from tracing_rca.analysis.rca import get_root_cause
from tracing_rca.rules.parser import get_rules

cwd = os.getcwd()

class TestCircularDetection(unittest.TestCase):
    """Checks if a circular dependency can be detected by the systems."""

    def test(self):
        """Runs the test."""

        parser = get_parser()
        data = ""
        testdata_path = os.path.join(cwd, "tests/test_circular.json")
        with open(testdata_path, 'r') as f:
            data = json.loads(f.read())

        traces_raw = parser.parse_spans(data)      
        traces = []

        with self.assertRaises(ValueError):
            for trace_id, spans in traces_raw.items():
                traces.append(Trace(trace_id, spans))


class TestFollowsFromRelation(unittest.TestCase):
    """Checks if the FollowsFrom Relations are correctly analyzed."""

    def test(self):
        """Runs the test."""
        rules = get_rules()

        parser = get_parser()
        data = ""
        testdata_path = os.path.join(cwd, "tests/test_follows_from.json")
        with open(testdata_path, 'r') as f:
            data = json.loads(f.read())

        traces_raw = parser.parse_spans(data)      
        traces = []

        for trace_id, spans in traces_raw.items():
            traces.append(Trace(trace_id, spans))

        for trace in traces:
            for span in trace.spans:
                for rule in rules:
                    rule.perform(span)
                
            trace.set_error_count()

            get_root_cause(trace.root_span)

            strands = [[span.span_id for span in strand] for strand in trace.get_error_strands()]

            assert ['1.2'] in strands, 'Span 1.2 should be considered independent'
            assert ['1.0', '1.3', '1.1'] in strands, 'The other strands should be considered dependent'
            assert len(strands) == 2, 'There should be exactly 2 failure strands recognized'


class TestChildOfRelation(unittest.TestCase):
    """Checks if the ChildOf Relations are correctly analyzed."""

    def test(self):
        """Runs the test."""
        rules = get_rules()

        parser = get_parser()
        data = ""
        testdata_path = os.path.join(cwd, "tests/test_child_of.json")
        with open(testdata_path, 'r') as f:
            data = json.loads(f.read())

        traces_raw = parser.parse_spans(data)      
        traces = []

        for trace_id, spans in traces_raw.items():
            traces.append(Trace(trace_id, spans))

        for trace in traces:
            for span in trace.spans:
                for rule in rules:
                    rule.perform(span)
                
            trace.set_error_count()

            get_root_cause(trace.root_span)

            strands = [[span.span_id for span in strand] for strand in trace.get_error_strands()]

            assert ['1.2', '1.1'] in strands, ''
            assert ['1.3', '1.4'] in strands, ''
            assert len(strands) == 2, 'There should be exactly 2 failure strands recognized'


if __name__ == '__main__':
    unittest.main()