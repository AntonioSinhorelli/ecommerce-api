from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def healthcheck(_request):
    return JsonResponse({'status': 'ok', 'projeto': 'ecommerce', 'api': '/api/', 'versao': 'v4'})


urlpatterns = [
    path('', healthcheck),
    path('admin/', admin.site.urls),
    path('api/', include('vendas.urls')),
]
