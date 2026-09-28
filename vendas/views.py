from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Cliente, Pedido
from .serializers import ClienteSerializer, PedidoSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    """
    CRUD de clientes.

    GET    /api/clientes/               lista
    POST   /api/clientes/               cria
    GET    /api/clientes/{id}/          detalhe (inclui resumo dos pedidos)
    PUT    /api/clientes/{id}/          atualiza
    PATCH  /api/clientes/{id}/          atualiza parcialmente
    DELETE /api/clientes/{id}/          remove (bloqueado se o cliente tiver pedidos)
    GET    /api/clientes/{id}/pedidos/  pedidos completos do cliente
    """

    queryset = Cliente.objects.prefetch_related('pedidos')
    serializer_class = ClienteSerializer

    @action(detail=True, methods=['get'])
    def pedidos(self, request, pk=None):
        cliente = self.get_object()
        serializer = PedidoSerializer(cliente.pedidos.all(), many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        cliente = self.get_object()
        if cliente.pedidos.exists():
            return Response(
                {'detail': 'Cliente possui pedidos e não pode ser removido. Desative-o (ativo=false).'},
                status=409,
            )
        return super().destroy(request, *args, **kwargs)


class PedidoViewSet(viewsets.ModelViewSet):
    """
    CRUD de pedidos. Filtros opcionais por query string:
    /api/pedidos/?cliente=1  e/ou  /api/pedidos/?status=PAGO
    """

    serializer_class = PedidoSerializer

    def get_queryset(self):
        qs = Pedido.objects.select_related('cliente')
        cliente = self.request.query_params.get('cliente')
        status = self.request.query_params.get('status')
        if cliente:
            qs = qs.filter(cliente_id=cliente)
        if status:
            qs = qs.filter(status=status.upper())
        return qs
