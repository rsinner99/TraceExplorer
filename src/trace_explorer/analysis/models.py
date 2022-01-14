"""
This module defines all models and helper functions to have an object-oriented
representation of the data to analyze.
"""
import re

from trace_explorer.definitions import tags, logs, http
from trace_explorer.definitions import span as span_def

from trace_explorer.queries import get_query
from trace_explorer.parsers import get_parser

class Span:
    """Represents a span within a trace which was produced by an E2E-Test"""

    def __init__(self, trace_id, span_id, span_data: dict):
        """
        Forcing KeyError if key does not exist
        """
        self.span_id = span_id
        self.trace_id = trace_id
        self.operation_name = span_data[span_def.OPERATION_NAME]
        self.start_time = span_data[span_def.START_TIME]
        self.duration = span_data[span_def.DURATION]
        self.end_time = self.start_time + self.duration # both values must be in microseconds
        self.service = span_data[span_def.SERVICE_NAME]
        self.tags = span_data[span_def.TAGS]
        self.logs = span_data.get(span_def.LOGS, []) # do not raise KeyError if logs are missing
        self.references = span_data[span_def.REFERENCES]
        self.error = self.has_error()
        self.children = []
        self.parent = None
        self.previous = None # reference to previous span in same hierarchy level
        self.type = span_def.SPAN_TYPE_ROOT # either root, child or follower
        self.stack = None
        self.cause = self.get_possible_root_cause()
        self.rating = 0 # integer rating for root-cause propability
        self.caused = None
        self.caused_by = None # reference to a span which is closer to the root cause

    def __dict__(self):
        return {
            'spanID': self.span_id,
            'operationName': self.operation_name,
            'duration': self.duration,
            'error': self.error,
            'rating': self.rating,
            'cause': self.cause,
            'type': self.type,
            'tags': self.tags,
            'logs': self.logs,
            'stack': self.stack,
            'children': [child.__dict__() for child in self.children]
        }

    def __str__(self):
        """
        Makes JSON serialization possible.
        """
        return self.span_id

    def __tree__(self):
        """Return a hierarchical representation of the causal relationship."""
        name = f'{self.span_id} - {self.operation_name}'
        return {
             name: {
                 'children': [child.__tree__() for child in self.children]
             }
        }

    def has_error(self):
        """Checks wheter the span contains an error or not."""
        if self.tags.get(tags.ERROR_KEY):
            return True
        if self.tags.get(tags.HTTP_STATUS_CODE_KEY) == http.STATUS_500:
            if not self.cause:
                self.cause = 'HTTP 500, but no error messages found!'
            return True
        return False

    def has_children(self):
        """States wheter the span has children or not."""
        return bool(self.children)

    def set_parent(self, parent):
        """Sets a pointer to the parent span."""
        if isinstance(parent, Span):
            if self.parent is None:
                self.parent = parent
            else:
                raise ValueError('Circular dependency detected')
        else:
            raise TypeError(f"Input must be of type 'Span' not {str(type(parent))}")

    def add_child(self, child):
        """Add a child of type child to the parent."""
        child.set_parent(self)
        child.type= span_def.SPAN_TYPE_CHILD
        self.children.append(child)

    def add_follower(self, follower):
        """Add a child of type follower to the parent."""
        follower.set_parent(self)
        follower.type = span_def.SPAN_TYPE_FOLLOWER
        self.children.append(follower)

    def get_possible_root_cause(self):
        """
        Earliest log with event='error' will be considered as root-cause of span failure.
        """
        only_errors = list(
            filter(
                lambda log: log[logs.FIELDS][logs.FIELD_EVENT] == logs.FIELD_EVENT_ERROR,
                self.logs
            )
        )
        sorted_list = sorted(only_errors, key=lambda log: log['timestamp'])
        if len(sorted_list) > 0:
            self.cause_timestamp = sorted_list[0]['timestamp']
            log_fields = sorted_list[0]['fields']
            self.stack = log_fields.get('stack', None)
            return log_fields.get('error.object') \
                if log_fields.get('error.object') else log_fields.get('message')

        return None


    def get_caused_strand(self):
        """
        Return a list of related spans with errors which
        where produced by the current span.
        """
        strand = []
        if self.caused:
            strand.extend(self.caused.get_caused_strand())
        elif not self in strand:
            strand.append(self)
        return strand


class Trace:
    """Represents a trace which was produced by an E2E-Test"""

    def __init__(self, trace_id, spans):
        self.error_count = 0
        self.trace_id = trace_id
        self.spans = self.init_spans(spans)
        self.resolve_relations()
        self.root_span = self.get_root_span()
        self.start_time = self.get_start_time()
        self.order_children(self.root_span)
        self.filename = f'trace_{self.trace_id}.html'

    def __str__(self):
        """
        Makes JSON serialization possible.
        """
        return self.trace_id

    def __dict__(self):
        return {
            'traceID': self.trace_id,
            'errorCount': self.error_count,
            'startTime': self.start_time,
            'filename': self.filename
        }

    def init_spans(self, spans):
        """
        Initializes Span-objects from their dictionary representation
        and returns a list of those Span-objects.
        """
        result = []
        for span_id, span in spans.items():
            obj = Span(self.trace_id, span_id, span)
            if obj.error:
                self.error_count += 1
            result.append(obj)
        return result

    def add_span(self, span_id, span_data):
        """
        Adds a new span to the existing trace.
        """
        span = Span(self.trace_id, span_id, span_data)
        if span.error:
            self.error_count += 1
        self.spans.append(span)
        return span

    def set_error_count(self):
        error_spans = list(filter(lambda span: span.error, self.spans))
        self.error_count = len(error_spans)

    def get_start_time(self):
        """Return the start time of the trace."""
        return self.root_span.start_time

    def get_root_span(self):
        """Return the root-span of a trace"""
        root = list(filter(lambda span: span.type == span_def.SPAN_TYPE_ROOT, self.spans))

        if len(root) > 1:
            raise ValueError("Found multiple root spans. Analysis should be done manually")
        if len(root) == 0:
            raise ValueError("Did not find a root span. Analysis should be done manually")

        return root[0]

    def resolve_relations(self):
        """Resolves the references of all spans in the trace."""
        for span in self.spans:
            for ref in span.references:
                self.resolve_reference(span, ref)

    def resolve_reference(self, span, reference):
        """
        Resolves the string-based reference of a span
        to point to the span instance of the reference.
        """
        ref_id = reference.get(span_def.SPAN_ID)
        ref_type = reference.get(span_def.REF_TYPE_KEY)
        parent = list(filter(lambda span: span.span_id == ref_id, self.spans))

        if len(parent) > 1:
            raise ValueError("Found spans with same ID. SpanIDs have to be unique!")
        if len(parent) < 1:
            try:
                query = get_query()
                parser = get_parser()
                data = query.get_span_from_storage(ref_id)
                span_dict = parser.parse_spans(data)[self.trace_id]
                parent = [self.add_span(ref_id, span_dict[ref_id])]
            except Exception as e:
                raise ValueError(f"Found a reference to a not existing span!: {ref_id}")

        if ref_type == span_def.REF_TYPE_CHILD_OF:
            parent[0].add_child(span)
        elif ref_type == span_def.REF_TYPE_FOLLOWS_FROM:
            parent[0].add_follower(span)

    def order_children(self, span):
        """
        Orders the children of a span by their start_time.
        Sets a pointer to the previous span the remain the order.
        """
        sorted_children = sorted(span.children, key=lambda span: span.start_time)
        for i, child in enumerate(sorted_children):
            if i > 0:
                child.previous = sorted_children[i-1]
            self.order_children(child)

    def get_error_strands(self):
        """
        Return a list of independent error strands starting
        from the most likely root-cause.
        """
        strands = []
        rc_spans = list(    # filter for spans which contain an error
            filter(         #  and did not cause errors in other spans.
                lambda span: span.error and not span.caused_by, self.spans
            )
        )
        for span in rc_spans:
            strand = [span]
            strand.extend([span for span in span.get_caused_strand() if not span in strand])
            strands.append(strand)
        return strands


class Szenario:
    """Represents a test execution of an E2E-Test"""

    def __init__(self, name, errors, failures):
        self.name = name
        self.errors = errors
        self.failures = failures
        self.traces = []
        self.traces_error_count = 0

    def __dict__(self):
        traces_with_error = [trace.__dict__() for trace in self.traces if trace.error_count > 0]
        return {
            'name': self.name,
            'errors': self.errors,
            'failures': self.failures,
            'traces': traces_with_error,
            'tracesCount': len(self.traces),
            'errorsCount': len(traces_with_error),
            'test_error': self.has_error(),
            'test_failed': self.has_failed()
        }

    def add_trace(self, trace: Trace):
        """Adding a trace to the list of traces in the szenario."""
        self.traces.append(trace)
        self.traces_error_count += trace.error_count

    def has_error(self):
        return not bool(re.match(r'^\[\]$', self.errors))

    def has_failed(self):
        return not bool(re.match(r'^\[\]$', self.failures))
