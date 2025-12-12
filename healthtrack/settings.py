from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Intentamos obtener la SECRET_KEY de las variables de entorno, si no existe usamos la insegura por defecto
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-u=l49+nd!qe04$h7u0%qzap-u12w&hy^k435*p=r78t4__h_t2')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'account',
    'home',
    'panel',
    'reportes',
    'seguimiento',
    'admin_panel',
    'professional_panel',
    'perfiles',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'account.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'healthtrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'healthtrack', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                'healthtrack.context_processors.user_navigation_context',
                'healthtrack.context_processors.user_profile_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'healthtrack.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') #Directorio donde se almacenan los archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' #Almacenamiento de archivos estáticos

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# URL al que redirige @login_required cuando el usuario no está autenticado
LOGIN_URL = 'account:login'

# Hacer que la sesión expire al cerrar el navegador (para pedir login de nuevo)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

API_BASE_URL = os.environ.get("API_URL", "http://localhost:3000/api").strip()

AUTHENTICATION_BACKENDS = [
    'account.backend.NodeAPIBackend',
]
API_URL = API_BASE_URL

# --- AJUSTES PARA CLOUD RUN / FIREBASE ---
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# 1. Motor de Sesiones (Stateless - Cookies Firmadas)
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# 2. Configuración Dinámica de Seguridad
CSRF_TRUSTED_ORIGINS = [
    'https://health-track-165f2.web.app', 
    'https://healthtrack-django-370777291529.us-central1.run.app',
    'https://healthtrack-django-6hbw54wrza-uc.a.run.app'
]

# --- CONFIGURACIÓN CRÍTICA PARA CLOUD RUN ---
# Forzamos la detección de HTTPS y Cookies Seguras
# Esto soluciona el problema de "is_secure() = False" detrás del proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = True

# Cookies
SESSION_COOKIE_NAME = '__session' 

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax' 
