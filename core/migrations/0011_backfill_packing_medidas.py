"""
Data migration: maps legacy diametro/alto_item values into the new
medida_1 / medida_2 DecimalField columns for existing PackingListItem rows.
Non-numeric values (e.g. '2"') are stored as None to avoid errors.
"""
from django.db import migrations


def _to_decimal(val):
    """Convert a string value to Decimal, returning None if not numeric."""
    if not val:
        return None
    import re
    # Keep only digits, dot and comma; replace comma by dot
    v = re.sub(r'[^0-9.,]', '', str(val)).replace(',', '.')
    if not v:
        return None
    try:
        from decimal import Decimal
        return Decimal(v)
    except Exception:
        return None


def backfill_medidas(apps, schema_editor):
    PackingListItem = apps.get_model('core', 'PackingListItem')
    items = PackingListItem.objects.filter(medida_1__isnull=True)
    to_update = []
    for item in items:
        m1 = _to_decimal(item.diametro)
        m2 = _to_decimal(item.alto_item)
        if m1 is not None or m2 is not None:
            item.medida_1 = m1
            item.medida_2 = m2
            to_update.append(item)
    if to_update:
        PackingListItem.objects.bulk_update(to_update, ['medida_1', 'medida_2'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_add_cotizacion_guia_packing_medidas'),
    ]

    operations = [
        migrations.RunPython(backfill_medidas, migrations.RunPython.noop),
    ]
