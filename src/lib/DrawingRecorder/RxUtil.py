# -*- coding: utf-8 -*-
"""Rx/schema loading/validation helpers"""

# local modules
import Paths

# system modules
import Rx
import yaml


# Globals
_RX = Rx.Factory({'register_core_types': True})
_SCHEMA_CACHE = {}


# Implementation
def _get_schema(name):
    if name not in _SCHEMA_CACHE:
        path = Paths.join(Paths.RX, name + '.rx.yaml')
        schema = _RX.make_schema(yaml.safe_load(open(path, 'r')))
        _SCHEMA_CACHE[name] = schema
    return _SCHEMA_CACHE[name]


def load_yaml(schema, path):
    scm = _get_schema(schema)
    data = yaml.safe_load(open(path, 'r'))
    return data if scm.check(data) else None
