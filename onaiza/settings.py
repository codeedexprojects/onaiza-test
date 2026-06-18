from django.utils.translation import ugettext_lazy as _
from datetime import timedelta
from pathlib import Path
from decouple import config, Csv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-6fgn@gaj_&_p3pnit#)3y--ud^@ry6$1hu^nl(wjkqrt!+ggx8')

DEBUG = config('DEBUG', cast=bool)
SERVER = config('SERVER', cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

PLACES_MAPS_API_KEY = config('PLACES_MAPS_API_KEY', default='')

INSTALLED_APPS = [
    'registration',
    'dal',
    'dal_select2',
    'versatileimagefield',
    'rest_framework',
    'el_pagination',
    'django_template_maths',
    'pwa',
    'keyboard_shortcuts',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    'main',
    'users',
    'products',
    'warehouses',
    'staffs',
    'general',
    'sales',
    'purchases',
    'customers',
    'vendors',
    'suppliers',
    'finance',
    'orders',
    'web',
    'offers',
    'delivery_agent',
    'reports',
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
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'onaiza.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [Path(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'web.context_processors.web_context',
                'main.context_processors.main_context',
            ],
        },
    },
]


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=210),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=730),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 2,
}

WSGI_APPLICATION = 'onaiza.wsgi.application'

_DATABASE_URL = config('DATABASE_URL', default=None)
_DB_ENGINE = config('DB_ENGINE', default='postgresql')

if _DATABASE_URL:
    import dj_database_url
    DATABASES = {'default': dj_database_url.parse(_DATABASE_URL, conn_max_age=600)}
elif _DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            # 'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT'),
        }
    }

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

LOCALE_PATHS = (
    Path(BASE_DIR, 'locale'),
)
LANGUAGES = (
    ('ml', _('Malayalam')),
    ('en', _('English')),
)
LANGUAGE_CODE = 'en-us'

LOGIN_URL = '/app/accounts/login/'
LOGOUT_URL = '/app/accounts/logout/'
LOGIN_REDIRECT_URL = '/app/dashboard/'
LOGOUT_REDIRECT_URL = ''

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(BASE_DIR, "media")
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_FILE_ROOT = Path(BASE_DIR, "static")
STATICFILES_DIRS = (
    Path(BASE_DIR, "static"),
)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'


# PWA_SERVICE_WORKER_PATH = Path(BASE_DIR, 'static/js', 'serviceworker.js')
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static/js', 'serviceworker.js')
PWA_APP_NAME = 'Onaiza'
PWA_APP_DESCRIPTION = "ONAIZA PWA"
PWA_APP_THEME_COLOR = '#000000'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/en/app/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/en/app/'
PWA_APP_STATUS_BAR_COLOR = 'orange'

PWA_APP_ICONS = [
    {
        'src': '/static/web/images/icons/onaiza-fav-icon.png',
        'sizes': '160x160'
    },
    {
        "src": "/static/web/images/icons/android-chrome-192x192.png",
        "sizes": "192x192",
        "type": "image/png"
    },
    {
        "src": "/static/web/images/icons/android-chrome-512x512.png",
        "sizes": "512x512",
        "type": "image/png",
    },
    {
        "src": "/static/web/images/icons/android-chrome-maskable-192x192.png",
        "sizes": "192x192",
        "type": "image/png",
        "purpose": "maskable"
    },
    {
        "src": "/static/web/images/icons/android-chrome-maskable-512x512.png",
        "sizes": "512x512",
        "type": "image/png",
        "purpose": "maskable"
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/web/images/icons/onaiza-fav-icon.png',
        'sizes': '160x160'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/images/icon.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'
# =========PWA END========

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

VERSATILEIMAGEFIELD_SETTINGS = {
    'cache_length': 2592000,
    'cache_name': 'versatileimagefield_cache',
    'jpeg_resize_quality': 70,
    'sized_directory_name': '__sized__',
    'filtered_directory_name': '__filtered__',
    'placeholder_directory_name': '__placeholder__',
    'create_images_on_demand': True,
    'image_key_post_processor': None,
    'progressive_jpeg': False
}


PASSWORD_ENCRYPTION_KEY = config('PASSWORD_ENCRYPTION_KEY', default='')
RZP_ID_KEY = config('RZP_ID_KEY', default='')
RZP_SECRET_KEY = config('RZP_SECRET_KEY', default='')


# START keyboard_shortcuts settings #
HOTKEYS = [
    {
        'keys': 'g + h',  # go home
        'link': '/'
    },
    {
        'keys': 'n + t ',  # go to create transaction
        'link': '/app/finance/create-transaction'
    },
]

SPECIAL_DISABLED = True
# END keyboard_shortcuts settings #

EL_PAGINATION_NEXT_LABEL = '>'
