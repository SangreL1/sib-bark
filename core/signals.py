"""
Señales de Django para el sistema SIB Bark.

Señal implementada:
  - post_save en OrdenCompra: detecta cambio de semáforo de Plazo
    (green → yellow o green/yellow → red) y envía alerta por correo,
    ademas de registrar el evento en el modelo Trazabilidad.

Para no disparar correos duplicados en cada guardado, el semáforo anterior
se compara contra el nuevo usando una cache in-memory por PK. En producción
con múltiples workers puede usarse django-cacheops/Redis; para el uso mono-
proceso actual esto es suficiente.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

# ─────────────────────────────────────────────────────────────────────────────
# Cache en memoria: { pk: semaforo_plazo_anterior }
# ─────────────────────────────────────────────────────────────────────────────
_semaforo_plazo_cache = {}


@receiver(pre_save, sender='core.OrdenCompra')
def capturar_semaforo_anterior(sender, instance, **kwargs):
    """Guarda el semáforo de plazo ANTES de guardar para poder compararlo."""
    if instance.pk:
        _semaforo_plazo_cache[instance.pk] = instance.semaforo_plazo


@receiver(post_save, sender='core.OrdenCompra')
def alerta_semaforo_plazo(sender, instance, created, **kwargs):
    """
    Tras guardar una OC, compara el semáforo anterior con el nuevo.
    Si cambió a un estado más crítico (yellow o red), envía correo
    y registra en Trazabilidad.
    """
    from .models import Trazabilidad  # importación diferida para evitar ciclos

    semaforo_nuevo = instance.semaforo_plazo
    semaforo_prev  = _semaforo_plazo_cache.pop(instance.pk, None)

    # Sin cambio o estado que no requiere alerta
    if semaforo_nuevo == semaforo_prev or semaforo_nuevo not in ('yellow', 'red'):
        return

    # Solo alertar si la situación empeoró (no si mejoró)
    orden_criticidad = {'grey': 0, 'green': 1, 'yellow': 2, 'red': 3}
    if orden_criticidad.get(semaforo_nuevo, 0) <= orden_criticidad.get(semaforo_prev, 0):
        return

    # ── Construir mensaje ────────────────────────────────────────────────────
    dias = instance.dias_restantes_calculado
    if semaforo_nuevo == 'yellow':
        asunto = f"[SIB Bark] ALERTA: OC {instance.numero_oc} vence en {dias} dias"
        cuerpo = (
            f"Estimado equipo,\n\n"
            f"La Orden de Compra N° {instance.numero_oc} ({instance.cliente}) "
            f"vence en {dias} dias hábiles (Fecha compromiso: {instance.fecha_compromiso}).\n\n"
            f"Por favor gestionar el despacho a la brevedad.\n\n"
            f"-- Sistema SIB Bark"
        )
        accion  = "Alerta Plazo Proximo"
        detalle = f"El semaforo de Plazo cambio a AMARILLO. Vencimiento en {dias} dias."
    else:  # red
        asunto = f"[SIB Bark] URGENTE: OC {instance.numero_oc} ATRASADA"
        cuerpo = (
            f"Estimado equipo,\n\n"
            f"La Orden de Compra N° {instance.numero_oc} ({instance.cliente}) "
            f"Esta ATRASADA. Fecha compromiso: {instance.fecha_compromiso} "
            f"({abs(dias)} dias de retraso).\n\n"
            f"-- Sistema SIB Bark"
        )
        accion  = "Alerta Plazo Vencido"
        detalle = f"El semaforo de Plazo cambio a ROJO. La OC lleva {abs(dias)} dias de retraso."

    # ── Enviar correo ────────────────────────────────────────────────────────
    destinatarios = getattr(settings, 'RESPONSABLES_EMAIL', [])
    if destinatarios:
        try:
            send_mail(
                subject=asunto,
                message=cuerpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=destinatarios,
                fail_silently=True,
            )
        except Exception:
            pass  # Nunca romper el flujo principal por un fallo de correo

    # ── Registrar en Trazabilidad ────────────────────────────────────────────
    try:
        Trazabilidad.objects.create(
            orden_compra=instance,
            usuario=None,       # disparo automático (sin usuario)
            accion=accion,
            detalle=detalle,
        )
    except Exception:
        pass
