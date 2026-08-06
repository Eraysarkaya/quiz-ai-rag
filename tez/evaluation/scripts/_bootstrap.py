"""
Path bootstrap helpers for thesis evaluation scripts.

These helpers make the scripts independent from the current working
directory by always resolving imports from the real project root.
"""

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
EVALUATION_ROOT = SCRIPT_DIR.parent
TEZ_ROOT = EVALUATION_ROOT.parent
PROJECT_ROOT = TEZ_ROOT.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
EVALUATION_SRC = EVALUATION_ROOT / "src"


def bootstrap_paths(include_backend: bool = False) -> None:
    """Add stable import roots for evaluation scripts."""
    evaluation_src = str(EVALUATION_SRC)
    backend_root = str(BACKEND_ROOT)

    if evaluation_src not in sys.path:
        sys.path.insert(0, evaluation_src)
    if include_backend:
        if backend_root not in sys.path:
            sys.path.insert(0, backend_root)
