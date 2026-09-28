"""
Testes do app vendas.  Executar com:  python manage.py test vendas
"""
from decimal import Decimal
from io import StringIO
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.models import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Cliente, Pedido


def _cliente(**extra):
    dados = {'nome': 'Maria Silva', 'email': 'maria@email.com', 'cpf': '123.456.789-00', 'estado': 'RJ'}
    dados.update(extra)
    return Cliente.objects.create(**dados)


class HealthcheckTests(TestCase):
    def test_raiz_retorna_200(self):
        response = APIClient().get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')


class RelacionamentoTests(TestCase):
    def test_cliente_tem_varios_pedidos(self):
        cliente = _cliente()
        Pedido.objects.create(cliente=cliente, valor_total=Decimal('100.00'), endereco_entrega='Rua A, 1')
        Pedido.objects.create(cliente=cliente, valor_total=Decimal('50.00'), endereco_entrega='Rua A, 1')
        self.assertEqual(cliente.pedidos.count(), 2)

    def test_nao_apaga_cliente_com_pedidos(self):
        cliente = _cliente()
        Pedido.objects.create(cliente=cliente, valor_total=Decimal('10.00'), endereco_entrega='Rua A, 1')
        with self.assertRaises(ProtectedError):
            cliente.delete()


class ClienteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_cria_e_lista_clientes(self):
        response = self.client.post('/api/clientes/', {
            'nome': 'João Souza', 'email': 'joao@email.com', 'cpf': '111.222.333-44', 'estado': 'sp',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['estado'], 'SP')

        response = self.client.get('/api/clientes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_email_duplicado_retorna_400(self):
        _cliente()
        response = self.client.post('/api/clientes/', {
            'nome': 'Outra', 'email': 'maria@email.com', 'cpf': '999.999.999-99',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_detalhe_inclui_pedidos(self):
        cliente = _cliente()
        Pedido.objects.create(cliente=cliente, valor_total=Decimal('99.90'), endereco_entrega='Rua B, 2')
        data = self.client.get(f'/api/clientes/{cliente.id}/').json()
        self.assertEqual(data['total_pedidos'], 1)
        self.assertEqual(data['pedidos'][0]['valor_total'], '99.90')

    def test_rota_pedidos_do_cliente(self):
        cliente = _cliente()
        Pedido.objects.create(cliente=cliente, valor_total=Decimal('20.00'), endereco_entrega='Rua C')
        response = self.client.get(f'/api/clientes/{cliente.id}/pedidos/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['cliente_nome'], 'Maria Silva')

    def test_delete_cliente_com_pedidos_retorna_409(self):
        cliente = _cliente()
        Pedido.objects.create(cliente=cliente, valor_total=Decimal('20.00'), endereco_entrega='Rua C')
        self.assertEqual(self.client.delete(f'/api/clientes/{cliente.id}/').status_code, 409)

    def test_delete_cliente_sem_pedidos(self):
        cliente = _cliente()
        self.assertEqual(self.client.delete(f'/api/clientes/{cliente.id}/').status_code, 204)


class PedidoApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cliente = _cliente()

    def test_crud_pedido(self):
        response = self.client.post('/api/pedidos/', {
            'cliente': self.cliente.id, 'valor_total': '250.00',
            'forma_pagamento': 'CARTAO', 'endereco_entrega': 'Av. Rio Branco, 100',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        pedido_id = response.json()['id']
        self.assertEqual(response.json()['status'], 'PENDENTE')

        response = self.client.patch(f'/api/pedidos/{pedido_id}/', {'status': 'PAGO'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status_display'], 'Pago')

        self.assertEqual(self.client.delete(f'/api/pedidos/{pedido_id}/').status_code, 204)

    def test_valor_negativo_retorna_400(self):
        response = self.client.post('/api/pedidos/', {
            'cliente': self.cliente.id, 'valor_total': '-1.00', 'endereco_entrega': 'Rua X',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_filtros(self):
        outro = _cliente(email='b@b.com', cpf='000.000.000-01')
        Pedido.objects.create(cliente=self.cliente, valor_total=1, endereco_entrega='x', status='PAGO')
        Pedido.objects.create(cliente=outro, valor_total=1, endereco_entrega='x')
        self.assertEqual(len(self.client.get(f'/api/pedidos/?cliente={outro.id}').json()), 1)
        self.assertEqual(len(self.client.get('/api/pedidos/?status=pago').json()), 1)


class AdminTests(TestCase):
    @mock.patch.dict(os.environ, {'DJANGO_SUPERUSER_USERNAME': 'root', 'DJANGO_SUPERUSER_PASSWORD': 'Senha@Forte1'})
    def test_criar_admin_e_login(self):
        call_command('criar_admin', stdout=StringIO())
        call_command('criar_admin', stdout=StringIO())  # idempotente
        self.assertEqual(get_user_model().objects.filter(username='root', is_superuser=True).count(), 1)

        self.assertTrue(self.client.login(username='root', password='Senha@Forte1'))
        for url in ('/admin/', '/admin/vendas/cliente/', '/admin/vendas/pedido/', '/admin/vendas/pedido/add/'):
            self.assertEqual(self.client.get(url).status_code, 200, url)
