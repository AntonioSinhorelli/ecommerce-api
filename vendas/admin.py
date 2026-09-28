from django.contrib import admin

from .models import Cliente, Pedido

admin.site.site_header = 'E-commerce - Administração'
admin.site.site_title = 'E-commerce Admin'
admin.site.index_title = 'Gestão de clientes e pedidos'


class PedidoInline(admin.TabularInline):
    model = Pedido
    extra = 0
    fields = ('status', 'forma_pagamento', 'valor_total', 'endereco_entrega')
    show_change_link = True


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'cpf', 'cidade', 'estado', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'estado')
    search_fields = ('nome', 'email', 'cpf')
    inlines = [PedidoInline]


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'status', 'forma_pagamento', 'valor_total', 'data_pedido')
    list_filter = ('status', 'forma_pagamento', 'data_pedido')
    search_fields = ('cliente__nome', 'cliente__email', 'id')
    list_select_related = ('cliente',)
    autocomplete_fields = ('cliente',)
