'''
Test settings. Activated through pytest.ini_options in pyproject.toml
'''
from .base import *  # noqa: F401, F403

DEBUG = False

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
