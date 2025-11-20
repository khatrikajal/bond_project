# # /root/bond_platform/Backend/config/settings/local.py
# from os import getenv, path
# from dotenv import load_dotenv
# from .base import * # noqa
# from .base import BASE_DIR

# # local_env_file = path.join(BASE_DIR, ".env",".env.local")
# local_env_file = path.join(BASE_DIR.parent, "envs", ".env.local")

# if path.isfile(local_env_file):
#     load_dotenv(local_env_file)


# # SECRET_KEY = "django-insecure-z(alis=n7f+*r8==1e1qee2z!l80j#wd#onby7pj--)u76g6xl"

# SECRET_KEY = getenv("SECRET_KEY")
# SITE_NAME = getenv("SITE_NAME", "Bond Platform")

# # SECURITY WARNING: don't run with debug turned on in production!
# # DEBUG = getenv("DEBUG") 

# # SITE_NAME = getenv("SITE_NAME")

# DEBUG = getenv("DEBUG", "False").lower() == "true"
# # ALLOWED_HOSTS = ["bondplatform.com", "localhost", "127.0.0.1"]
# # ALLOWED_HOSTS = ["bondplatform.com", "localhost", "127.0.0.1", "127.0.0.1:8000","93.127.206.37:8000"]
# # ALLOWED_HOSTS = ["bondplatform.com", "localhost", "127.0.0.1", "127.0.0.1:8000","93.127.206.37"]
# ALLOWED_HOSTS = [ "localhost", "127.0.0.1", "93.127.206.37","*"]

# # CSRF_TRUSTED_ORIGINS = [
# #     "http://localhost:8000",
# #     "http://127.0.0.1:8000",
# #     "http://93.127.206.37:8000",
# #     "https://93.127.206.37:8000",
# # ]


# CSRF_TRUSTED_ORIGINS = [
#     "http://localhost:8000",
#     "http://127.0.0.1:8000",

#     "http://93.127.206.37:8000",
#     "https://93.127.206.37:8000",
#     "http://localhost:3040",
#     "http://93.127.206.37:4000",
# ]

# # ALLOWED_HOSTS = ['*']


# ADMIN_URL = getenv("ADMIN_URL")


# # EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"
# # EMAIL_HOST = getenv("EMAIL_HOST")
# # EMAIL_PORT = getenv("EMAIL_PORT")
# # DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL")
# # DOMAIN = getenv("DOMAIN")

# # Email Configuration (from .env.local)
# EMAIL_BACKEND = getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
# EMAIL_HOST = getenv("EMAIL_HOST", "smtp.gmail.com")
# EMAIL_PORT = int(getenv("EMAIL_PORT", 587))
# EMAIL_USE_TLS = getenv("EMAIL_USE_TLS", "True").lower() == "true"
# EMAIL_USE_SSL = getenv("EMAIL_USE_SSL", "False").lower() == "true"
# EMAIL_HOST_USER = getenv("EMAIL_HOST_USER", "")
# EMAIL_HOST_PASSWORD = getenv("EMAIL_HOST_PASSWORD", "")
# DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL", "no-reply@yourdomain.com")
# ADMIN_EMAIL = getenv("ADMIN_EMAIL", "admin@yourdomain.com")
# DOMAIN = getenv("DOMAIN", "localhost:8000")


# MAX_UPLOAD_SIZE = 1 * 1024 * 1024  # 5MB

# # JWT Settings - CRITICAL: Set the signing key
# SIMPLE_JWT.update({
#     "SIGNING_KEY": SECRET_KEY,  # Use the SECRET_KEY from environment
#     "AUTH_COOKIE_SECURE": False,  # Allow non-HTTPS in development
#     "AUTH_COOKIE_DOMAIN": None,   # No domain restriction in development
#     "AUTH_COOKIE_SAMESITE":"Lax",
#     "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),  # 1 hour for development
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # 1 day for development
# })

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True


# # Celery Configuration
# CELERY_BROKER_URL = getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
# CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# # Development-specific settings
# REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
#     "rest_framework.renderers.JSONRenderer",
#     "rest_framework.renderers.BrowsableAPIRenderer",  # Enable browsable API in development
# ]

# # CACHES = {
# #     "default": {
# #         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
# #         "LOCATION": "unique-snowflake",
# #     }
# # }

# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "unique-snowflake",
#     },
#     "otp": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "otp-snowflake",
#     },
# }


# CORS_ALLOW_ALL_ORIGINS = False  

# /root/bond_platform/Backend/config/settings/local.py
from os import getenv, path
from dotenv import load_dotenv
from .base import * # noqa
from .base import BASE_DIR
import pytesseract
import platform

local_env_file = path.join(BASE_DIR.parent, "envs", ".env.local")


# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Detect OS and set Tesseract path
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
if path.isfile(local_env_file):
    load_dotenv(local_env_file)

SECRET_KEY = getenv("SECRET_KEY")
SITE_NAME = getenv("SITE_NAME", "Bond Platform")

DEBUG = getenv("DEBUG", "False").lower() == "true"

# Allowed hosts
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "93.127.206.37", "*"]

# CSRF trusted origins - include both backend and frontend URLs
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3040",
    "http://127.0.0.1:3040",
    "http://93.127.206.37:8000",
    "http://93.127.206.37:3040",
    "http://93.127.206.37:4000",
]

ADMIN_URL = getenv("ADMIN_URL")

# Email Configuration
EMAIL_BACKEND = getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = getenv("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_HOST_USER = getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL", "no-reply@yourdomain.com")
ADMIN_EMAIL = getenv("ADMIN_EMAIL", "admin@yourdomain.com")
DOMAIN = getenv("DOMAIN", "localhost:8000")

MAX_UPLOAD_SIZE = 1 * 1024 * 1024  # 1MB

JWT_SECRET_KEY = getenv("JWT_SECRET_KEY", SECRET_KEY)
# JWT Settings - CRITICAL: Set the signing key
# SIMPLE_JWT.update({
#     "SIGNING_KEY": JWT_SECRET_KEY,  # Use the SECRET_KEY from environment SECRET_KEY,
#     "AUTH_COOKIE_SECURE": True,  # Allow non-HTTPS in development
#     "AUTH_COOKIE_DOMAIN": None,   # No domain restriction in development
#     "AUTH_COOKIE_SAMESITE": "Strict",
#     "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),  # 1 hour for development
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # 1 day for development
#     "USER_ID_FIELD": "user_id",        # <-- important
#     "USER_ID_CLAIM": "user_id",  
# })
SIMPLE_JWT = {
    "SIGNING_KEY": JWT_SECRET_KEY,
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    # Cookies setup (for frontend integration)
    "AUTH_COOKIE": "access_token",
    "AUTH_COOKIE_REFRESH": "refresh_token",
    "AUTH_COOKIE_SECURE": False,  # True only on HTTPS
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "Lax",
}
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# ==========================================
# CRITICAL: CORS Configuration for Server
# ==========================================
# REMOVE CORS_ALLOW_ALL_ORIGINS from base.py or override it here
CORS_ALLOW_ALL_ORIGINS = False  # Must be False when using credentials

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3040",
    "http://127.0.0.1:3040",
    "http://93.127.206.37:3040",  # Your frontend port
    "http://93.127.206.37:3000",
    "http://93.127.206.37:4000",  # Alternative frontend port
    "http://localhost:3000",      # Development
    "http://127.0.0.1:3000",
    "http://localhost:3030",
    "http://127.0.0.1:5500"
]

# CRITICAL: Must be True for cookie-based authentication
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# ==========================================
# JWT Settings for Cookie-Based Auth
# ==========================================
# SIMPLE_JWT.update({
#     "SIGNING_KEY": SECRET_KEY,
#     # CRITICAL: Must be False for HTTP connections
#     "AUTH_COOKIE_SECURE": False,  # Set to True only when using HTTPS
#     "AUTH_COOKIE_DOMAIN": None,   # No domain restriction
#     # CRITICAL: Must be "Lax" or "None" for cross-origin requests
#     "AUTH_COOKIE_SAMESITE": "Lax",  # Changed from "Strict"
#     "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
#     "AUTH_COOKIE_HTTP_ONLY": True,
#     "AUTH_COOKIE_PATH": "/",
# })

# Session and CSRF cookies - Must match JWT cookie settings
SESSION_COOKIE_SECURE = False  # False for HTTP
CSRF_COOKIE_SECURE = False     # False for HTTP
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Celery Configuration
CELERY_BROKER_URL = getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny', 
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.authentication.throttling.OtpThrottle",
     
    ],
    "DEFAULT_THROTTLE_RATES": {
        "otp": "5/minute",
        
    },
    # Custom exception handler
    "EXCEPTION_HANDLER": "config.common.exceptions.custom_exception_handler",
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    },
    "otp": {
        "BACKEND": "django_redis.cache.RedisCache",  
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/2"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "otp",
        "TIMEOUT": 600,
    }
}

