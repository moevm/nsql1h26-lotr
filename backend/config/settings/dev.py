'''
Dev settings/ User in Docker and when launching locally.
Activated through DJANGO_SETTINGS_MODULE=config.settings.dev
'''
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['*']

SPECTACULAR_SETTINGS['SERVERS'] = [  # noqa: F405
    {'url': 'http://localhost:8000', 'description': 'Local Docker'}
]
