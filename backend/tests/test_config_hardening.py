import os
import pytest
from config import validate_production_secret


def test_validate_production_secret_in_development():
    # Should not raise in development even if empty or insecure
    validate_production_secret("", "development")
    validate_production_secret("dev-secret-key-change-in-production", "development")
    validate_production_secret("short", "development")


def test_validate_production_secret_missing_in_production():
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_secret("", "production")
    assert "CRITICAL CONFIGURATION ERROR" in str(exc_info.value)
    assert "SECRET_KEY environment variable is required" in str(exc_info.value)


def test_validate_production_secret_insecure_default_in_production():
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_secret("dev-secret-key-change-in-production", "production")
    assert "CRITICAL CONFIGURATION ERROR" in str(exc_info.value)
    # Ensure raw secret is not leaked in error message
    assert "dev-secret-key-change-in-production" not in str(exc_info.value)


def test_validate_production_secret_too_short_in_production():
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_secret("short-secret-under-32-chars", "production")
    assert "CRITICAL CONFIGURATION ERROR" in str(exc_info.value)
    assert "at least 32 characters" in str(exc_info.value)
    # Ensure candidate secret is not leaked in error message
    assert "short-secret-under-32-chars" not in str(exc_info.value)


def test_validate_production_secret_valid_in_production():
    secure_key = "a" * 32
    # Should not raise
    validate_production_secret(secure_key, "production")
    validate_production_secret(secure_key, "prod")
