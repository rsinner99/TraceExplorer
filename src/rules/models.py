"""This module implements all models for a rule-based analysis."""

import re

class Rule:
    """Rule for usage on a span."""
    def __init__(self, name, category, conditions, actions):
        self.name = name
        self.category = category
        self.conditions = conditions
        self.actions = actions

    def perform(self, span):
        """Execute the rule."""
        for condition in self.conditions:
            if not condition.check(span):
                return
        for action in self.actions:
            action.execute(span)


class Condition:
    """A condition to match on a span."""
    def __init__(self, data):
        self.location = data["location"] # either tags or logs
        self.field = data["field"]
        self.match = data["match"] # regular expression

    def check(self, span):
        """Check if the condition matches on the span."""
        result = None
        field_value = ''
        if self.location == 'tags':
            field_value = span.tags.get(self.field, '')
            result = re.match(self.match, str(field_value))
        elif self.location == 'logs':
            for log in span.logs:
                field_value = log['fields'].get(self.field, '')
                result = re.match(self.match, str(field_value))
                if result:
                    break

        return bool(result)


class Action:
    """Defines an action to be performed on a span."""
    def __init__(self, data):
        self.type = data["type"] # either children or parent
        self.match = [] # list of conditions
        for raw_condition in data["match"]:
            self.match.append(Condition(raw_condition))
        self.cause = data["cause"]

    def prepare_cause(self, span):
        """Return a formatted cause for the failure."""
        fields_regex = r"{([^}]+)}"
        results = []
        fields = re.findall(fields_regex, self.cause)
        for field in fields:
            f_type, f_field = field.split(':')
            if f_type == 'tags':
                results.append(span.tags.get(f_field, ''))
            elif f_type == 'logs':
                results.append(span.logs.get(f_field, ''))
        return re.sub(fields_regex, '{}', self.cause).format(*results)

    def execute(self, span):
        """Perform an action depending on the type."""
        if self.type == 'children':
            self.check_children(span)
        elif self.type == 'parent':
            self.check_parent(span)
        elif self.type == 'self':
            self.check_self(span)
        elif self.type == 'no-children':
            self.check_no_children(span)

    def check_no_children(self, span):
        """Check if span has children."""
        if len(span.children) == 0:
            span.error = True
            span.cause = self.prepare_cause(span)

    def check_children(self, span):
        """Perform a condition check on the spans children."""
        for child in span.children:
            matched = True
            for condition in self.match:
                if not condition.check(child):
                    matched = False
                    break
            if matched:
                child.cause = self.prepare_cause(child)
                # to be changed. Hier liegt ja eigentlich kein Fehler vor oder doch?!
                child.error = True
            self.check_children(child)

    def check_parent(self, span):
        """Perform a condition check on the spans parent."""
        if span.parent:
            matched = True
            for condition in self.match:
                if not condition.check(span.parent):
                    matched = False
                    break
            if matched:
                span.parent.cause = self.prepare_cause(span.parent)
                span.parent.error = True

    def check_self(self, span):
        """Perform a condition check on the span itself."""
        matched = True
        for condition in self.match:
            if not condition.check(span.parent):
                matched = False
                break
        if matched:
            span.cause = self.prepare_cause(span)
            span.error = True
