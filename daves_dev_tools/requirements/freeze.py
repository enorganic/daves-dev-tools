"""
This module now simply wraps `dependence.freeze` (for backwards compatibility)
"""

from typing import List

from dependence.freeze import freeze, get_frozen_requirements, main

__all__: List[str] = [
    "main",
    "freeze",
    "get_frozen_requirements",
]

if __name__ == "__main__":
    main()
