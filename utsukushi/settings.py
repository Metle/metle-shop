from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = '6ag@o==h8q1*=4qz4u0)_9qoll^6a9e(@g#j@$25^#c)s&cl*h'
# SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = list(config('ALLOWED_HOSTS', default='', cast=Csv()))

for vercel_host_var in (
    'VERCEL_URL',
    'VERCEL_BRANCH_URL',
    'VERCEL_PROJECT_PRODUCTION_URL',
):
    vercel_host = config(vercel_host_var, default='')
    if vercel_host and vercel_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(vercel_host)

CSRF_TRUSTED_ORIGINS = list(config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv(),
))

for host in ALLOWED_HOSTS:
    if host in {'127.0.0.1', 'localhost'} or host.startswith('.'):
        continue

    origin = f'https://{host}'
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'cart',
    'accounts',
    'orders',
    'utsukushi',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'utsukushi.urls'

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
                'store.context_processors.brands_nav',
            ],
        },
    },
]

WSGI_APPLICATION = 'utsukushi.wsgi.application'
ASGI_APPLICATION = 'utsukushi.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST'),
#         'PORT': config('DB_PORT'),
#     }
# }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
LANGUAGES = [
    ('en', 'English'),
    ('nl', 'Dutch'),
]
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_build'
LOCALE_PATHS = [BASE_DIR / 'locale']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
