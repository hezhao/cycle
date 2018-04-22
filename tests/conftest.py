import pytest
from app import app


@pytest.fixture
def test_app():
    test_app = app.test_client()
    test_app.testing = True
    return test_app
