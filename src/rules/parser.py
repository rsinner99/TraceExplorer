"""
This module helps to parse and initialize all rules in the specified directory.
"""

import json
import os
from ..config import RULE_BASE_DIR
from .models import Rule, Condition, Action

def parse(data):
    """Returns a list of rule object from the raw list of rules."""
    data = json.loads(data)
    rules = []
    for name, pattern in data.items():
        conditions = []
        actions = []
        for raw_condition in pattern.get('conditions'):
            conditions.append(Condition(raw_condition))
        for raw_action in pattern.get('actions'):
            actions.append(Action(raw_action))
        rules.append(Rule(name, pattern.get('category'), conditions, actions))

    return rules

def get_rules():
    """Returns a list of all rules in the rule directory."""
    rules = []
    for filename in os.listdir(RULE_BASE_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(RULE_BASE_DIR, filename), 'r', encoding='utf-8') as file:
                rules.extend(parse(file.read()))
    return rules
