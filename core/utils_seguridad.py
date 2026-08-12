"""
Utilidades de Ciberseguridad — SIB Bark
Validación de RUT chileno usando el algoritmo Módulo 11.
"""
import re


def _limpiar_rut(rut: str) -> str:
    """Elimina puntos, guiones y espacios del RUT."""
    return re.sub(r'[\.\-\s]', '', rut).upper().strip()


def validar_rut_chileno(rut: str) -> bool:
    """
    Valida un RUT chileno usando el algoritmo Módulo 11.
    Acepta formatos: '12345678-9', '12.345.678-9', '123456789', etc.
    Retorna True si el RUT es matemáticamente válido, False si no.
    """
    if not rut:
        return False

    rut_limpio = _limpiar_rut(rut)

    if len(rut_limpio) < 2:
        return False

    # Separar cuerpo y dígito verificador
    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]

    # Validar que el cuerpo sea numérico
    if not cuerpo.isdigit():
        return False

    # Validar rango mínimo (RUTs válidos tienen al menos 7 dígitos en el cuerpo)
    if len(cuerpo) < 7 or len(cuerpo) > 8:
        return False

    # Calcular dígito verificador esperado con Módulo 11
    numero = int(cuerpo)
    suma = 0
    multiplo = 2

    while numero != 0:
        suma += (numero % 10) * multiplo
        numero //= 10
        multiplo = multiplo + 1 if multiplo < 7 else 2

    resultado = 11 - (suma % 11)

    if resultado == 11:
        dv_esperado = '0'
    elif resultado == 10:
        dv_esperado = 'K'
    else:
        dv_esperado = str(resultado)

    return dv_ingresado == dv_esperado


def formatear_rut(rut: str) -> str:
    """
    Formatea un RUT al estilo estándar chileno: XX.XXX.XXX-X.
    El RUT debe ser válido antes de formatearlo.
    """
    rut_limpio = _limpiar_rut(rut)
    if len(rut_limpio) < 2:
        return rut

    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]

    # Formatear con puntos
    cuerpo_formateado = ''
    for i, digito in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0:
            cuerpo_formateado = '.' + cuerpo_formateado
        cuerpo_formateado = digito + cuerpo_formateado

    return f"{cuerpo_formateado}-{dv}"
