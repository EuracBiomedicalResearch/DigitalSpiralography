# -*- coding: utf-8 -*-
"""Drawing factory"""

# local modules
import Drawing


# drawing ID/s constructors table
id_table = {
    "DSPR1": lambda: Drawing.Spiral(
        "DSPR1", Drawing.SpiralParams(radius=65, turns=5., direction="CW")),
    "DSPR2": lambda: Drawing.Spiral(
        "DSPR2", Drawing.SpiralParams(radius=65, turns=5., direction="CW"))}


# implementation
def from_id(id):
    if id not in id_table:
        return None
    return id_table[id]()
