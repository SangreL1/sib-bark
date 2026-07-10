from django.contrib import admin
from .models import (
    AFP, Empleado, Asistencia, TablaImpuestoUnico, 
    ParametroLegal, LiquidacionSueldo, HaberAdicional, DescuentoAdicional
)

@admin.register(AFP)
class AFPAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'comision_porcentaje', 'vigente_desde')
    search_fields = ('nombre',)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'cargo', 'tipo_contrato', 'activo')
    list_filter = ('tipo_contrato', 'sistema_salud', 'activo', 'unidad_negocio')
    search_fields = ('nombre_completo', 'rut')

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha', 'tipo', 'horas_trabajadas', 'horas_extra')
    list_filter = ('tipo', 'fecha')
    date_hierarchy = 'fecha'

@admin.register(TablaImpuestoUnico)
class TablaImpuestoUnicoAdmin(admin.ModelAdmin):
    list_display = ('mes_vigencia', 'valor_utm', 'tramo_desde_utm', 'tramo_hasta_utm', 'factor', 'rebaja')
    list_filter = ('mes_vigencia',)

@admin.register(ParametroLegal)
class ParametroLegalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'porcentaje', 'valor_moneda', 'vigente_desde')
    list_filter = ('vigente_desde',)
    search_fields = ('nombre',)

class HaberAdicionalInline(admin.TabularInline):
    model = HaberAdicional
    extra = 1

class DescuentoAdicionalInline(admin.TabularInline):
    model = DescuentoAdicional
    extra = 1

@admin.register(LiquidacionSueldo)
class LiquidacionSueldoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'mes', 'anio', 'sueldo_base', 'liquido_a_pago')
    list_filter = ('mes', 'anio')
    inlines = [HaberAdicionalInline, DescuentoAdicionalInline]
    readonly_fields = (
        'total_imponible', 'total_no_imponible', 'total_haberes',
        'descuento_afp', 'descuento_salud', 'descuento_cesantia',
        'impuesto_unico', 'total_descuentos', 'liquido_a_pago', 'total_tributable'
    )
