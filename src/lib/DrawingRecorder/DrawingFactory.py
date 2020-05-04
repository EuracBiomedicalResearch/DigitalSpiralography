# -*- coding: utf-8 -*-
"""Drawing factory"""

# local modules
from . import Drawing


# drawing ID/s constructors table
id_table = {
    "DSPR1": lambda: Drawing.Spiral(
        "DSPR1", (216, 136), Drawing.SpiralParams(
            radius=65, turns=5., direction="CW")),
    "DSPR2": lambda: Drawing.Spiral(
        "DSPR2", (325, 203), Drawing.SpiralParams(
            radius=65, turns=5., direction="CW")),
    "DSPR3": lambda: Drawing.Spiral(
        "DSPR3", (311, 216), Drawing.SpiralParams(
            radius=65, turns=5., direction="CW"))}


# implementation
def from_id(id):
    if id not in id_table:
        return None
    return id_table[id]()
