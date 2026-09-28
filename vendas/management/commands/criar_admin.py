"""
Cria (ou atualiza) o superusuário do Django Admin a partir de variáveis de ambiente.

Variáveis:
    DJANGO_SUPERUSER_USERNAME  (padrão: admin)
    DJANGO_SUPERUSER_EMAIL     (padrão: admin@ecommerce.com)
    DJANGO_SUPERUSER_PASSWORD  (obrigatória - sem ela nada é criado)

Uso:  python manage.py criar_admin
É idempotente: pode rodar em todo deploy sem duplicar o usuário.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria/atualiza o superusuário (admin) a partir das variáveis DJANGO_SUPERUSER_*'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@ecommerce.com')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

        if not password:
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_PASSWORD não definida - superusuário não foi criado.'
            ))
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        acao = 'criado' if created else 'atualizado'
        self.stdout.write(self.style.SUCCESS(f'Superusuário "{username}" {acao} com sucesso.'))
