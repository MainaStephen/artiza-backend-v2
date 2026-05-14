from pathlib import Path
from datetime import timedelta
import os

# -------------------------------------------------
# BASE DIRECTORY
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------
# SECURITY
# -------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "replace-this-with-env-secret")
DEBUG = True

# ALLOWED_HOSTS = [
#     '146.190.52.91',  # server IP
#     'localhost',
#     '127.0.0.1',
#     '[::1]',
#     'artiza.co.ke',
#     'www.artiza.co.ke',
#     'web', 
# ]

# -------------------------------------------------
# CORS & CSRF
# -------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://146.190.52.91:3000",
    "http://146.190.52.91",
    "https://artiza.co.ke",
    "https://www.artiza.co.ke",
    "https://artiza.co.ke:8000",
]
CORS_ALLOW_CREDENTIALS = True

# CSRF_TRUSTED_ORIGINS = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     "http://146.190.52.91:3000",
#     "http://146.190.52.91",
#     "https://artiza.co.ke",
#     "https://www.artiza.co.ke",
# ]
ALLOWED_HOSTS = [
    '146.190.52.91',
    'localhost',
    '127.0.0.1',
    'artiza.co.ke',
    'www.artiza.co.ke',
]

CSRF_TRUSTED_ORIGINS = [
    'http://146.190.52.91',
    'https://artiza.co.ke',
    'https://www.artiza.co.ke',
]


# -------------------------------------------------
# APPLICATIONS
# -------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    'users',
    'projects',
    'proposals',
    'updates',
    'reviews',
    'portfolio',
    'negotiations',
    'notifications',
    'cart',
    'checkout',
    'artisanmatching',
    'artisanapplication',
     
    # "notifications.apps.NotificationsConfig",
]

ASGI_APPLICATION = "artiza.asgi.application"

# -------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------
MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",  
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------------------------------
# TEMPLATES
# -------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # required for admin
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# -------------------------------------------------
# URLS / WSGI
# -------------------------------------------------
ROOT_URLCONF = 'artiza.urls'
WSGI_APPLICATION = 'artiza.wsgi.application'

# -------------------------------------------------
# DATABASE
# -------------------------------------------------
import os

DATABASES = {
    'default': {
        'ENGINE': os.environ.get("SQL_ENGINE", "django.db.backends.postgresql"),
        'NAME': os.environ.get("SQL_DATABASE", "artiza_db"),
        'USER': os.environ.get("SQL_USER", "postgresuser"),
        'PASSWORD': os.environ.get("SQL_PASSWORD", "postgrespassword"),
        'HOST': os.environ.get("SQL_HOST", "db"),
        'PORT': os.environ.get("SQL_PORT", "5432"),
    }
}



# -------------------------------------------------
# EMAIL CONFIGURATION
# -------------------------------------------------


DEFAULT_FROM_EMAIL='artizakenya@gmail.com'


BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# -------------------------------------------------
# AUTH / USERS
# -------------------------------------------------
AUTH_USER_MODEL = "users.User"

# -------------------------------------------------
# REST FRAMEWORK
# -------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
}

# -------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -------------------------------------------------
# STATIC & MEDIA FILES
# -------------------------------------------------
STATIC_URL = "/backend-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Use Whitenoise for static files in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True




# -------------------------------------------------
# DEFAULT PRIMARY KEY FIELD TYPE
# -------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

