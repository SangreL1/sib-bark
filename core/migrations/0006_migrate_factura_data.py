"""
Data migration: migra los datos del campo de texto factura_resumen (y fecha_factura)
de OrdenCompra al nuevo modelo Factura creado en 0005_factura_model.
Se crea una Factura por cada OC que tenga numero de factura registrado.
"""
from django.db import migrations
from decimal import Decimal


def migrar_facturas_desde_texto(apps, schema_editor):
    OrdenCompra = apps.get_model('core', 'OrdenCompra')
    Factura     = apps.get_model('core', 'Factura')

    migradas = 0
    for oc in OrdenCompra.objects.exclude(factura_resumen__isnull=True).exclude(factura_resumen=''):
        numero = (oc.factura_resumen or '').strip()
        if not numero:
            continue
        Factura.objects.create(
            orden_compra=oc,
            entrega=None,                        # sin entrega específica (datos legacy)
            numero_factura=numero,
            fecha_emision=oc.fecha_factura or oc.fecha_oc or oc.creado_en.date() if oc.creado_en else None,
            monto=oc.valor_total or Decimal('0.00'),
            estado='pendiente',                  # estado conservador por defecto
            url_externa=None,
            archivo=None,
        )
        migradas += 1

    print(f"  >> {migradas} facturas migradas desde factura_resumen.")


def revertir_migracion(apps, schema_editor):
    """En el rollback simplemente elimina los registros que creó esta migración."""
    Factura = apps.get_model('core', 'Factura')
    Factura.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_factura_model'),
    ]

    operations = [
        migrations.RunPython(migrar_facturas_desde_texto, revertir_migracion),
    ]
