"""
Global QSS Theme and Color Tokens for the PySide6 UI.
Provides the deep space base and glassmorphic styling tokens.
"""

# Color Tokens
BASE_BG = "#0c0914"
GLASS_BG = "rgba(22, 16, 36, 0.85)"
GLASS_BORDER = "rgba(168, 85, 247, 0.35)"
ACCENT_NEON = "#a855f7"
TEXT_PRIMARY = "#ffffff"
TEXT_PLACEHOLDER = "rgba(255, 255, 255, 0.6)"

GLOBAL_QSS = f"""
/* Deep Space Base Window */
QMainWindow {{
    background-color: {BASE_BG};
}}

/* Glassmorphic Card Containers */
QFrame.glass-card {{
    background-color: {GLASS_BG};
    border: 1px solid {GLASS_BORDER};
    border-radius: 12px;
}}

/* Mandatory High-Contrast Text Inputs */
QLineEdit, QComboBox, QSpinBox {{
    background-color: {GLASS_BG};
    border: 1.5px solid {ACCENT_NEON};
    color: {TEXT_PRIMARY};
    border-radius: 6px;
    padding: 6px;
}}

/* Placeholder text styling (Qt uses property overrides for placeholders but QSS is limited, 
so we set color generally, and rely on code-level placeholders if needed. But in PySide6, 
we can use the ::placeholder pseudo-state, though it might not be standard in all versions, 
it works in modern Qt6) */
QLineEdit::placeholder, QComboBox::placeholder {{
    color: {TEXT_PLACEHOLDER};
    font-style: italic;
}}

/* Global Typography */
* {{
    font-family: "Inter", "Outfit", "Segoe UI", sans-serif;
}}
"""
