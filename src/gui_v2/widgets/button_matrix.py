"""
ButtonMatrixWidget Wrapper module for gui_v2.
"""

import sys
import os

# Add root src directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from button_matrix import (
    ButtonMatrix as ButtonMatrixWidget, StandardButtonArray, ExtraButtonArray, ButtonPill
)

__all__ = ["ButtonMatrixWidget", "StandardButtonArray", "ExtraButtonArray", "ButtonPill"]
