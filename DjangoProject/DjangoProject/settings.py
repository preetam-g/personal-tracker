import os
from pathlib import Path
from dotenv import load_dotenv

# 1. PATHS
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. ENVIRONMENT LOADING
load_dotenv(BASE_DIR / ".env")

# 3. SECURITY
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-fallback-key")

# Set DEBUG to False in Render dashboard, True in your local .env
DEBUG = os.getenv("DEBUG", "False") == "True"

# 4. NETWORKING & ALLOWED HOSTS
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS = [RENDER_EXTERNAL_HOSTNAME]
    # Required for forms/login to work on Render's HTTPS
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
    'django.contrib.staticfiles',
    
    # Your Apps
    'apps.expenses',
    'apps.accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Crucial for CSS/JS on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DjangoProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DjangoProject.wsgi.application'

# 6. DATABASE (Using individual Postgres variables)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("POSTGRES_NAME"),
        'USER': os.getenv("POSTGRES_USER"),
        'PASSWORD': os.getenv("POSTGRES_PASSWORD"),
        'HOST': os.getenv("POSTGRES_HOST"),
        'PORT': os.getenv("POSTGRES_PORT", "5432"),
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 9. STATIC FILES (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
# This is the folder where Render will "collect" all your files
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Use WhiteNoise to serve compressed/cached files in production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 10. EMAIL SETUP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = f"Expense Tracker <{EMAIL_HOST_USER}>"

# 11. MISC
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'