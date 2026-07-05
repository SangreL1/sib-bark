from django.contrib import admin
from .models import OrdenCompra, FMR, Entrega, Costo, Trazabilidad, ItemOC, PackingListItem, Factura, CostoMaterial, CostoManoObra


# ─────────────────────────────────────────────────────────────────────────────
# Inlines
# ─────────────────────────────────────────────────────────────────────────────

class CostoMaterialInline(admin.TabularInline):
    model = CostoMaterial
    extra = 0
    fields = ('producto', 'cantidad', 'valor_unitario', 'proveedor', 'fecha_compra')


class CostoManoObraInline(admin.TabularInline):
    model = CostoManoObra
    extra = 0
    fields = ('cargo', 'cargo_otro', 'precio_hora', 'horas_normales', 'horas_extra', 'cantidad_trabajadores')


class FacturaInline(admin.TabularInline):
    model = Factura
    extra = 0
    fields = ('numero_factura', 'fecha_emision', 'monto', 'estado', 'entrega', 'url_externa', 'archivo')


class EntregaInline(admin.TabularInline):
    model = Entrega
    extra = 0
    fields = ('fecha_entrega', 'guia_despacho', 'estado', 'cantidad_entregada')
    show_change_link = True


class ItemOCInline(admin.TabularInline):
    model = ItemOC
    extra = 0
    fields = ('linea', 'descripcion', 'cantidad', 'cantidad_entregada', 'precio_unitario')


class CostoInline(admin.TabularInline):
    model = Costo
    extra = 0
    fields = ('categoria', 'descripcion', 'monto', 'proveedor', 'fecha')


class PackingListItemInline(admin.TabularInline):
    model = PackingListItem
    extra = 0
    fields = ('item_oc', 'cantidad', 'numero_bulto', 'largo_mt', 'ancho_mt', 'alto_mt', 'peso_kg')


# ─────────────────────────────────────────────────────────────────────────────
# OrdenCompra
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display  = ('numero_oc', 'cliente', 'estado', 'prioridad', 'porcentaje_entregado',
                     'valor_total', 'fecha_compromiso', 'semaforo_plazo')
    list_filter   = ('estado', 'prioridad', 'cliente')
    search_fields = ('numero_oc', 'cliente', 'proyecto', 'descripcion',
                     'facturas__numero_factura', 'fmrs__fmr_code')
    ordering      = ('-fecha_oc',)
    inlines       = [ItemOCInline, EntregaInline, FacturaInline, CostoInline, CostoMaterialInline, CostoManoObraInline]

    fieldsets = (
        ('Identificación', {
            'fields': ('numero_oc', 'cliente', 'proyecto', 'descripcion')
        }),
        ('Fechas y Plazos', {
            'fields': ('fecha_oc', 'fecha_compromiso', 'tiempo_fabricacion', 'estado', 'prioridad')
        }),
        ('Financiero', {
            'fields': ('valor_total', 'guia_despacho_resumen', 'factura_resumen', 'fecha_factura')
        }),
        ('Documentos (Links)', {
            'classes': ('collapse',),
            'fields': ('oc_link', 'plano_link', 'cotizacion_link', 'excel_link', 'dossier_link', 'fmr_link')
        }),
        ('Documentos (Archivos)', {
            'classes': ('collapse',),
            'fields': ('oc_file', 'plano_file', 'cotizacion_file', 'excel_file', 'dossier_file', 'fmr_file')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )

    @admin.display(description='Semaforo Plazo')
    def semaforo_plazo(self, obj):
        colores = {'green': '🟢', 'yellow': '🟡', 'red': '🔴', 'grey': '⚫'}
        return colores.get(obj.semaforo_plazo, '?')


# ─────────────────────────────────────────────────────────────────────────────
# Factura
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display  = ('numero_factura', 'orden_compra', 'fecha_emision', 'monto', 'estado', 'entrega')
    list_filter   = ('estado',)
    search_fields = ('numero_factura', 'orden_compra__numero_oc', 'orden_compra__cliente')
    ordering      = ('-fecha_emision',)


# ─────────────────────────────────────────────────────────────────────────────
# Modelos secundarios
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(FMR)
class FMRAdmin(admin.ModelAdmin):
    list_display  = ('fmr_code', 'orden_compra', 'fecha', 'cotizacion', 'factura')
    search_fields = ('fmr_code', 'orden_compra__numero_oc', 'factura')


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display  = ('guia_despacho', 'orden_compra', 'fecha_entrega', 'estado')
    list_filter   = ('estado',)
    search_fields = ('guia_despacho', 'orden_compra__numero_oc')
    inlines       = [PackingListItemInline]


@admin.register(Costo)
class CostoAdmin(admin.ModelAdmin):
    list_display  = ('categoria', 'descripcion', 'monto', 'proveedor', 'fecha', 'orden_compra')
    list_filter   = ('categoria',)
    search_fields = ('descripcion', 'proveedor', 'orden_compra__numero_oc')


@admin.register(Trazabilidad)
class TrazabilidadAdmin(admin.ModelAdmin):
    list_display  = ('fecha_hora', 'orden_compra', 'accion', 'usuario')
    list_filter   = ('accion',)
    search_fields = ('orden_compra__numero_oc', 'accion', 'detalle')
    readonly_fields = ('fecha_hora',)


@admin.register(ItemOC)
class ItemOCAdmin(admin.ModelAdmin):
    list_display  = ('linea', 'descripcion', 'cantidad', 'cantidad_entregada', 'orden_compra')
    search_fields = ('descripcion', 'codigo', 'orden_compra__numero_oc')
