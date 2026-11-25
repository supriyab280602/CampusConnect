import os
from dotenv import load_dotenv

load_dotenv()

INSECURE_DEFAULT_SECRETS = {
    'dev-secret-key-change-in-production',
    'secret',
    'secretkey',
    'changeme',
    'password',
    'default',
    'admin',
}


def validate_production_secret(secret_key: str, env: str) -> None:
    """Validate that SECRET_KEY is set and cryptographically adequate in production.

    Refuses application startup if the secret is missing, matches known insecure defaults,
    or contains fewer than 32 characters. Under no circumstances is the key value logged
    or exposed in error messages.
    """
    if env.lower() in ('production', 'prod'):
        if not secret_key or not secret_key.strip():
            raise RuntimeError(
                "CRITICAL CONFIGURATION ERROR: SECRET_KEY environment variable is required in production. Application startup aborted."
            )
        cleaned = secret_key.strip()
        if (
            len(cleaned) < 32
            or cleaned in INSECURE_DEFAULT_SECRETS
            or 'change-in-production' in cleaned.lower()
            or 'dev-secret' in cleaned.lower()
        ):
            raise RuntimeError(
                "CRITICAL CONFIGURATION ERROR: SECRET_KEY must be a cryptographically secure string of at least 32 characters in production. Application startup aborted."
            )


class Config:
    ENV = os.getenv('FLASK_ENV', os.getenv('ENV', 'development')).lower()

    # Development fallback preserved; production requires explicit, hardened secret
    _raw_secret = os.getenv('SECRET_KEY')
    if ENV in ('production', 'prod'):
        validate_production_secret(_raw_secret or '', ENV)
        SECRET_KEY = _raw_secret
    else:
        SECRET_KEY = _raw_secret if _raw_secret else 'dev-secret-key-change-in-production'

    FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')
    PORT = int(os.getenv('PORT', '5000'))
    DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'instance', 'campusconnect.db'))
