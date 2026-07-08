from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def clp(value):
    if value is None or value == "":
        return "$0"
    try:
        # Convertir a float / int / Decimal
        val_number = int(round(float(value)))
        # Formatear con separador de miles usando comas, y luego cambiar comas por puntos
        formatted = f"{val_number:,}".replace(",", ".")
        return f"${formatted}"
    except (ValueError, TypeError):
        return f"${value}"
