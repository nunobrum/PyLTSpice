# -*- coding: utf-8 -*-
"""
*(Deprecated)*
Supporting Legacy import clauses. This will disappear in future versions
"""
print("Deprecation Warning! This will no longer be supported in future versions.\n"
      "Use 'from PyLTSpice import SimCommander' for a direct import of the LTSpice/NGSpice batch run class.")

from .sim.sim_batch import SimCommander