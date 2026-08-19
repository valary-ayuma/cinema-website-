"""Compatibility proxy for the third-party :mod:`celery` package.

The project used a root-level ``celery.py`` file, which otherwise shadows the
installed package whenever Django starts from this directory.
"""
import importlib.machinery
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent
_search_paths = [path for path in sys.path if Path(path or ".").resolve() != _project_root]
_spec = importlib.machinery.PathFinder.find_spec("celery", _search_paths)
if _spec is None or _spec.loader is None:
    raise ImportError("The Celery package is not installed.")

__file__ = _spec.origin
__path__ = list(_spec.submodule_search_locations or [])
__package__ = "celery"
_spec.loader.exec_module(sys.modules[__name__])
