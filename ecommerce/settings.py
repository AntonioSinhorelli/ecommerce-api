"""
Configurações do projeto Django "ecommerce".

Todas as configurações sensíveis vêm de variáveis de ambiente:
- Localmente: arquivo .env na raiz (veja .env.example).
- No Elastic Beanstalk: Configuration > Updates, monitoring, and logging > Environment properties.
"""
import os
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """Carrega um arquivo .env simples (CHAVE=valor) sem sobrescrever variáveis já definidas."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / '.env')


def _bool_env(name, default='False'):
    return os.getenv(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


def _list_env(name, default=''):
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


IS_TEST = 'test' in sys.argv

# ---------------------------------------------------------------------------
# Segurança básica
# ---------------------------------------------------------------------------
DEBUG = _bool_env('DJANGO_DEBUG', 'False')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG or IS_TEST:
        SECRET_KEY = 'django-insecure-somente-para-desenvolvimento-local'
    else:
        raise RuntimeError('SECRET_KEY não definida. Configure a variável de ambiente SECRET_KEY.')

_default_hosts = 'localhost,127.0.0.1,testserver' if (DEBUG or IS_TEST) else '.elasticbeanstalk.com'
ALLOWED_HOSTS = _list_env('DJANGO_ALLOWED_HOSTS', _default_hosts)


def _ec2_private_ip():
    """
    O health check do Elastic Beanstalk / Load Balancer acessa a instância pelo IP privado.
    Adicionamos esse IP ao ALLOWED_HOSTS para o health check não receber 400 (Bad Request).
    Usa IMDSv2; fora da AWS simplesmente não encontra nada.
    """
    try:
        token_req = urllib.request.Request(
            'http://169.254.169.254/latest/api/token',
            method='PUT',
            headers={'X-aws-ec2-metadata-token-ttl-seconds': '60'},
        )
        token = urllib.request.urlopen(token_req, timeout=0.5).read().decode()
        ip_req = urllib.request.Request(
            'http://169.254.169.254/latest/meta-data/local-ipv4',
            headers={'X-aws-ec2-metadata-token': token},
        )
        return urllib.request.urlopen(ip_req, timeout=0.5).read().decode()
    except Exception:
        return None


if not DEBUG and not IS_TEST:
    _ip = _ec2_private_ip()
    if _ip:
        ALLOWED_HOSTS.append(_ip)

CSRF_TRUSTED_ORIGINS = _list_env('DJANGO_CSRF_TRUSTED_ORIGINS')

# HTTPS: só ative (DJANGO_SECURE_SSL_REDIRECT=True) se o ambiente tiver certificado SSL.
# O domínio padrão *.elasticbeanstalk.com responde apenas em HTTP; com cookies "secure"
# o login no Django Admin não funcionaria. Por isso o padrão é False.
USE_HTTPS = (not DEBUG) and _bool_env('DJANGO_SECURE_SSL_REDIRECT', 'False')
SECURE_SSL_REDIRECT = USE_HTTPS
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '31536000')) if USE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ---------------------------------------------------------------------------
# Aplicações
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'vendas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serve o CSS/JS do admin mesmo sem o nginx
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'ecommerce.wsgi.application'

# ---------------------------------------------------------------------------
# Banco de dados
#   1) Variáveis RDS_* presentes (EB com RDS)  -> MySQL no RDS
#   2) Variáveis MYSQL_* presentes (local)     -> MySQL local
#   3) Caso contrário                          -> SQLite (db.sqlite3)
# ---------------------------------------------------------------------------
MYSQL_OPTIONS = {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'", 'charset': 'utf8mb4'}

USE_RDS = all(os.getenv(v) for v in ('RDS_DB_NAME', 'RDS_USERNAME', 'RDS_PASSWORD', 'RDS_HOSTNAME'))
USE_MYSQL_LOCAL = all(os.getenv(v) for v in ('MYSQL_DATABASE', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_HOST'))

if USE_RDS and not IS_TEST:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('RDS_DB_NAME'),
            'USER': os.getenv('RDS_USERNAME'),
            'PASSWORD': os.getenv('RDS_PASSWORD'),
            'HOST': os.getenv('RDS_HOSTNAME'),
            'PORT': os.getenv('RDS_PORT', '3306'),
            'OPTIONS': MYSQL_OPTIONS,
        }
    }
elif USE_MYSQL_LOCAL and not IS_TEST:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('MYSQL_DATABASE'),
            'USER': os.getenv('MYSQL_USER'),
            'PASSWORD': os.getenv('MYSQL_PASSWORD'),
            'HOST': os.getenv('MYSQL_HOST'),
            'PORT': os.getenv('MYSQL_PORT', '3306'),
            'OPTIONS': MYSQL_OPTIONS,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    # API aberta (como no projeto de aula) para facilitar os testes da avaliação.
    # Para exigir login em escritas, troque por 'rest_framework.permissions.IsAuthenticatedOrReadOnly'.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# ---------------------------------------------------------------------------
# Internacionalização
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Arquivos estáticos (CSS/JS do Django Admin)
# O collectstatic copia tudo para a pasta "static". Essa é a pasta que o
# Elastic Beanstalk mapeia por padrão em /static; se o nginx não servir,
# o WhiteNoise serve pelo próprio Django.
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
