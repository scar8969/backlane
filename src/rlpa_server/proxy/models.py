"""Compatibility shim for the proxy package.

cores/a9_rlpa_server_core.py reaches its models with package-relative imports
("from .models import Route").  The built tree keeps the models at the project
root, so without this module the proxy catch-all raises ModuleNotFoundError
instead of returning its 404 JSON.  This shim hands the proxy package the same
four names; models.py is declared first, and build.py keeps the first owner, so
this module owns nothing.
"""
from ..models import AccessLog, Route, User, db
