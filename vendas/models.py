from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Cliente(models.Model):
    """Cliente da loja virtual (quem realiza as compras no e-commerce)."""

    nome = models.CharField('nome', max_length=150)
    email = models.EmailField('e-mail', unique=True)
    cpf = models.CharField('CPF', max_length=14, unique=True, help_text='Formato: 000.000.000-00')
    telefone = models.CharField('telefone', max_length=20, blank=True)
    endereco = models.CharField('endereço', max_length=255, blank=True)
    cidade = models.CharField('cidade', max_length=100, blank=True)
    estado = models.CharField('UF', max_length=2, blank=True)
    ativo = models.BooleanField('ativo', default=True)
    data_cadastro = models.DateTimeField('data de cadastro', auto_now_add=True)

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} <{self.email}>'


class Pedido(models.Model):
    """Pedido de compra feito por um Cliente (relação 1:N — um cliente tem vários pedidos)."""

    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        PAGO = 'PAGO', 'Pago'
        ENVIADO = 'ENVIADO', 'Enviado'
        ENTREGUE = 'ENTREGUE', 'Entregue'
        CANCELADO = 'CANCELADO', 'Cancelado'

    class FormaPagamento(models.TextChoices):
        PIX = 'PIX', 'Pix'
        CARTAO = 'CARTAO', 'Cartão de crédito'
        BOLETO = 'BOLETO', 'Boleto'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='cliente',
    )
    data_pedido = models.DateTimeField('data do pedido', auto_now_add=True)
    status = models.CharField('status', max_length=10, choices=Status.choices, default=Status.PENDENTE)
    forma_pagamento = models.CharField(
        'forma de pagamento', max_length=10, choices=FormaPagamento.choices, default=FormaPagamento.PIX
    )
    valor_total = models.DecimalField(
        'valor total (R$)',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    endereco_entrega = models.CharField('endereço de entrega', max_length=255)
    observacoes = models.TextField('observações', blank=True)

    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'
        ordering = ['-data_pedido']

    def __str__(self):
        return f'Pedido #{self.pk} - {self.cliente.nome} ({self.get_status_display()})'
