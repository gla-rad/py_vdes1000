# -*- coding: utf-8 -*-
"""
Utilities Module.

This module contains various utility functions and classes.

@author: Jan Safar

Copyright 2024 GLA Research and Development Directorate

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

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
