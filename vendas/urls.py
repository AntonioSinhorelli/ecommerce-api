from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet, PedidoViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'pedidos', PedidoViewSet, basename='pedido')

urlpatterns = [
    path('', include(router.urls)),
]
