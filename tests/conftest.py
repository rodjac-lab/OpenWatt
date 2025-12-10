"""Pytest fixtures anchored to the FastAPI app defined by the Spec-Kit."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
