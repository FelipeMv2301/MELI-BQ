"""
Django settings for meliBQ project.

Estructura y convenciones copiadas de `gestorBQ` (mismo stack: Django + templates + HTMX +
Tailwind CLI standalone). Ver `backlog_proyecto/plan-integracion-mercadolibre.md`.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# ── Seguridad / entorno ──────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-solo-para-desarrollo-local")
DEBUG = os.getenv("DEBUG", "True").strip().lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

if not DEBUG:
    # Mismo criterio que gestorBQ: el proxy (Caddy/Railway) termina el TLS antes de Django.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalogo_ml",
    "facturacion_ml",
    "cuentas",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ROOT_URLCONF = "meliBQ.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "meliBQ.wsgi.application"

# ── Base de datos ─────────────────────────────────────────────────────────────
# Mismo switch que gestorBQ: DATABASE_VERSION=SQLITE en dev, cualquier otro valor -> Postgres.
# SPK-MELI-8 (dónde se despliega) y SPK-MELI-5 (cómo se lee Stock-Service) definen si esto
# termina siendo la misma Postgres que otro proyecto o una propia — ver plan-integracion-mercadolibre.md.
DATABASE_VERSION = os.getenv("DATABASE_VERSION", "SQLITE")

if DATABASE_VERSION == "SQLITE":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {
                "timeout": 60,
                "init_command": "PRAGMA journal_mode=WAL;",
                "transaction_mode": "IMMEDIATE",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internacionalización ──────────────────────────────────────────────────────
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# ── Estáticos ──────────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Login — Google OAuth vía django-allauth ──────────────────────────────────
# Portado de gestorBQ/cuentas/adapters.py + gestorBQ/gestorBQ/settings.py. Restringe el acceso a
# cuentas @bioquimica.cl, tanto en el selector de Google (AUTH_PARAMS hd) como server-side
# (BioquimicaSocialAccountAdapter). Pendiente: crear/registrar el redirect URI de ESTE proyecto en
# el Google Cloud Console (mismo client OAuth de gestorBQ con un redirect URI nuevo, o uno propio —
# a decidir con Felipe, ver plan-integracion-mercadolibre.md).
SITE_ID = 1

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
DOMINIO_PERMITIDO = os.getenv("DOMINIO_PERMITIDO", "@bioquimica.cl")

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": GOOGLE_CLIENT_ID,
            "secret": GOOGLE_CLIENT_SECRET,
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"hd": "bioquimica.cl"},
    }
}

SOCIALACCOUNT_ONLY = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = "cuentas.adapters.BioquimicaSocialAccountAdapter"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True

ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*"]
ACCOUNT_LOGOUT_ON_GET = True

LOGIN_REDIRECT_URL = "/catalogo/"

# ── Integraciones externas ────────────────────────────────────────────────────
# Consumidas desde integraciones/*.py vía `from django.conf import settings`. Ver
# backlog_proyecto/plan-integracion-mercadolibre.md sección 10 para el contrato de cada una.

# Mercado Libre — SPK-MELI-1 pendiente (app/credenciales no creadas todavía)
ML_APP_ID = os.getenv("ML_APP_ID", "")
ML_APP_SECRET = os.getenv("ML_APP_SECRET", "")
ML_REDIRECT_URI = os.getenv("ML_REDIRECT_URI", "")
ML_SITE_ID = os.getenv("ML_SITE_ID", "MLC")

# WooCommerce — solo lectura (fotos + descripción por SKU). Resuelto 2026-08-20.
WOO_URL = os.getenv("WOO_URL", "")
WOO_KEY = os.getenv("WOO_KEY", "")
WOO_SECRET = os.getenv("WOO_SECRET", "")

# Stock-Service — SPK-MELI-5 pendiente (¿DB compartida o API REST?)
STOCKSERVICE_BASE_URL = os.getenv("STOCKSERVICE_BASE_URL", "")
STOCKSERVICE_API_KEY = os.getenv("STOCKSERVICE_API_KEY", "")

# SAP (vía Token-SAP-BQ, mismo patrón que gestorBQ/BQ-Integraciones)
TOKEN_SAP_BQ_URL = os.getenv("TOKEN_SAP_BQ_URL", "")
TOKEN_SAP_BQ_SERVICE_NAME = os.getenv("TOKEN_SAP_BQ_SERVICE_NAME", "")
TOKEN_SAP_BQ_PASSWORD = os.getenv("TOKEN_SAP_BQ_PASSWORD", "")
SAP_URL = os.getenv("SAP_URL", "")

# Facele/Docele — obtención de PDF de boleta/factura ya emitida (mismo cliente que BQ-Integraciones)
FACELE_URL = os.getenv("FACELE_URL", "")
FACELE_USER = os.getenv("FACELE_USER", "")
FACELE_PASSWORD = os.getenv("FACELE_PASSWORD", "")
FACELE_TAXID = os.getenv("FACELE_TAXID", "")

# ── Logging ────────────────────────────────────────────────────────────────────
# Por defecto, con DEBUG=False, Django solo intenta mandar los errores 500 por mail (mail_admins)
# y no imprime nada a consola — en Docker eso significa que `docker compose logs` no muestra el
# traceback real de un 500 (encontrado 2026-08-20 diagnosticando el primer 500 en meli-dev, hubo que
# reproducirlo a mano en el shell). Con esto, todo error queda en los logs del contenedor siempre.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
