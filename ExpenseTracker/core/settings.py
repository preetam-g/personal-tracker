import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# 1. PATHS
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. ENVIRONMENT LOADING
load_dotenv(BASE_DIR / ".env")

# 3. CORE SECURITY
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-fallback-key")

# Logic: DEBUG should be True locally, False on Render.
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
IS_PRODUCTION = os.getenv("IS_PRODUCTION", "False").lower() == "true"

# 4. NETWORKING
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS = [RENDER_EXTERNAL_HOSTNAME]
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}']
else:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# 5. APPLICATION DEFINITION
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    # Internal Apps
    'apps.expenses',
    'apps.accounts',
    'apps.base',
    'apps.ledger',
    'apps.forex',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# 6. DATABASE CONFIGURATION
# PROD: Uses Postgres (Render) | LOCAL: Uses SQLite for speed/simplicity
if IS_PRODUCTION:
    DATABASES = {
        'default': dj_database_url.parse(
            os.getenv("DATABASE_URL"),
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# 7. AUTHENTICATION
AUTH_USER_MODEL = "accounts.UserProfile"

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 8. INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# 9. STATIC & MEDIA FILES
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise Configuration for Production
if IS_PRODUCTION or not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 10. EMAIL SYSTEM
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # Real SMTP settings for production
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = f"Expense Tracker <{os.getenv('EMAIL_HOST_USER', 'noreply@example.com')}>"

# 11. SECURITY HARDENING (Production Only)
if IS_PRODUCTION:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# 12. MISC
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 13. FOREX
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
EXCHANGE_RATE_BASE_URL = os.getenv("EXCHANGE_RATE_BASE_URL")
EXCHANGE_RATE_API_TIMEOUT = 20

# 14. CACHE
if IS_PRODUCTION:
    cache_options = {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
        "CONNECTION_POOL_KWARGS": {
            "ssl_cert_reqs": None,
        },
    }
else:
    cache_options = {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
    }

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL"),
        "OPTIONS": cache_options,
        "TIMEOUT": 60 * 10,
    }
}