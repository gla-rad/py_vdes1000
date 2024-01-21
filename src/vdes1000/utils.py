# -*- coding: utf-8 -*-
"""
Misc. Utilities.

Created on Tue Jan 16 10:44:26 2024

@author: Jan Safar

"""
# =============================================================================
# %% Import Statements
# =============================================================================
from threading import Lock


# =============================================================================
# %% Function Definitions
# =============================================================================
print_lock = Lock()

def ts_print(*a, **b):
    """
    A thread-safe print() function.

    Attempts to prevent garbled output when printing to a console from multiple
    threads.

    """
    with print_lock:
        print(*a, **b)
