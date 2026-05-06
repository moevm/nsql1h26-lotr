'''
Base settings for all environments.
No default values for sevrets - KeyError on start is better than a working app
with empty SECRET_KEY
'''
import os
from pathlib import Path

from dotenv import load_dotenv


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR.parent / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG is redefined in dev.py / test.py
DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.users',
    'apps.pages',
    'apps.catalogs',
    'apps.analytics',
    'apps.bulk',
    'apps.meta',
    'apps.search',
    'apps.comments',
    'apps.categories'
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
# Ne4j is configured separately through neomodel, not DATABASES

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.getenv('DATABASE_URL', 'sqlite:////app/db/django.sqlite3')
                  .removeprefix('sqlite:///'),
    }
}

# Custom user model
AUTH_USER_MODEL = 'users.User'


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Neo4j / neomodel
# neomodel 6.x reads config through get_config()
def _configure_neomodel() -> None:
    from neomodel import config as neomodel_config  # type: ignore[attr-defined]

    neomodel_config.DATABASE_URL = os.environ['NEO4J_BOLT_URL']
    neomodel_config.MAX_CONNECTION_POOL_SIZE = int(
        os.getenv('NEO4J_MAX_POOL_SIZE', '50')
    )
    neomodel_config.FORCE_TIMEZONE = True


_configure_neomodel()


# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated'
    ),

    'EXCEPTION_HANDLER': 'config.exception_handler.custom_exception_handler',

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# JWT
from datetime import timedelta  # noqa: E402


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=int(os.getenv('ACCESS_TOKEN_LIFETIME_MINUTES', '15'))
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=int(os.getenv('REFRESH_TOKEN_LIFETIME_DAYS', '7'))
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainPairSerializer',
}

# CORS
# In base - locked. dev.py allows front on localhost:5173
CORS_ALLOWED_ORIGINS: list[str] = os.getenv(
    'CORS_ALLOWED_ORIGINS', ''
).split(',')
CORS_ALLOW_CREDENTIALS = True  # for Authorization header

# drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'LOTR Wiki API',
    'DESCRIPTION': 'Catalogue of Lord of the Rings universe entities',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication and user profile'},
        {'name': 'characters', 'description': 'Character catalogue'},
        {'name': 'locations', 'description': 'Location catalogue'},
        {'name': 'races', 'description': 'Race catalogue'},
        {'name': 'events', 'description': 'Event catalogue'},
        {'name': 'organizations', 'description': 'Organization catalogue'},
        {'name': 'timelines', 'description': 'Timeline catalogue'},
        {'name': 'items', 'description': 'Item catalogue'},
        {'name': 'languages', 'description': 'Language catalogue'},
        {'name': 'scripts', 'description': 'Script catalogue'},
        {'name': 'pages', 'description': 'Entity pages (generic)'},
        {'name': 'analytics', 'description': 'Graph analytics'},
        {'name': 'bulk', 'description': 'Import / Export'},
        {'name': 'meta', 'description': 'Metadata (node and relation types)'},
    ],
    'ENUM_GENERATE_CHOICE_DESCRIPTION': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':
                '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'neomodel': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
