from rest_framework import serializers

from .models import Cliente, Pedido


class PedidoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    forma_pagamento_display = serializers.CharField(source='get_forma_pagamento_display', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'cliente', 'cliente_nome', 'data_pedido',
            'status', 'status_display',
            'forma_pagamento', 'forma_pagamento_display',
            'valor_total', 'endereco_entrega', 'observacoes',
        ]
        read_only_fields = ['data_pedido']


class PedidoResumoSerializer(serializers.ModelSerializer):
    """Versão resumida do pedido, exibida dentro do Cliente."""

    class Meta:
        model = Pedido
        fields = ['id', 'data_pedido', 'status', 'valor_total']


class ClienteSerializer(serializers.ModelSerializer):
    pedidos = PedidoResumoSerializer(many=True, read_only=True)
    total_pedidos = serializers.IntegerField(source='pedidos.count', read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'email', 'cpf', 'telefone', 'endereco', 'cidade', 'estado',
            'ativo', 'data_cadastro', 'total_pedidos', 'pedidos',
        ]
        read_only_fields = ['data_cadastro']

    def validate_estado(self, value):
        return value.upper()
