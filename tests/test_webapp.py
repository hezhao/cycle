from app import app
import pytest


def test_index(test_app):
    res = test_app.get('/')
    assert res.status_code == 200
