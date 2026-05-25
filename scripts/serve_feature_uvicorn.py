#!/usr/bin/env python3
"""Start the Feast feature server with uvicorn (no gunicorn fork).

Gunicorn can interfere with MCP Streamable HTTP sessions in some clients.
Use this for local Cursor MCP development.
"""
import os
import sys

REPO = os.path.join(os.path.dirname(__file__), "..", "feature_repo")
sys.path.insert(0, os.path.abspath(REPO))

from feast import FeatureStore
from feast.feature_server import get_app
import uvicorn

if __name__ == "__main__":
    store = FeatureStore(repo_path=REPO)
    app = get_app(store)
    uvicorn.run(app, host="0.0.0.0", port=6566, access_log=True)
