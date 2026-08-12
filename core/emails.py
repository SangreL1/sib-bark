"""
Sistema de Emails Automáticos — Portal OC Clientes
Los destinatarios de notificaciones internas se leen desde ConfiguracionSistema en BD.
"""
from django.core.mail import send_mail
from django.conf import settings


def _get_destinatarios_internos():
    """
    Obtiene la lista de correos configurados en la BD para notificaciones internas.
    Si la tabla no existe o está vacía, usa el correo por defecto del settings.
    """
    try:
        from core.models import ConfiguracionSistema
        config = ConfiguracionSistema.get_instancia()
        if config.correos_notificacion_oc:
            correos = [
                c.strip()
                for c in config.correos_notificacion_oc.replace('\n', ',').split(',')
                if c.strip()
            ]
            if correos:
                return correos
    except Exception:
        pass
    # Fallback al settings
    return getattr(settings, 'RESPONSABLES_EMAIL', ['admi.bark@gmail.com'])


def _send_safe(subject, message, recipient_list, html_message=None):
    """Envía email capturando excepciones para no romper el flujo si hay error SMTP."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_message,
        )
        return True
    except Exception as e:
        print(f"[WARN] Error enviando email: {e}")
        return False


# ─────────────────────────────────────────────────────
# 1. Nueva solicitud de acceso → Staff Bark
# ─────────────────────────────────────────────────────
def email_nueva_solicitud_acceso(perfil):
    """Notifica al equipo Bark que un nuevo cliente solicitó acceso al portal."""
    destinatarios = _get_destinatarios_internos()
    subject = f"🆕 Solicitud de acceso al portal — {perfil.razon_social}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Portal OC Clientes</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <h3 style="color:#1e293b;">Nueva Solicitud de Acceso 🔔</h3>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px;color:#64748b;font-weight:bold;">Empresa:</td><td style="padding:8px;">{perfil.razon_social}</td></tr>
          <tr style="background:#f1f5f9;"><td style="padding:8px;color:#64748b;font-weight:bold;">RUT:</td><td style="padding:8px;">{perfil.rut}</td></tr>
          <tr><td style="padding:8px;color:#64748b;font-weight:bold;">Contacto:</td><td style="padding:8px;">{perfil.user.get_full_name() or perfil.user.username}</td></tr>
          <tr style="background:#f1f5f9;"><td style="padding:8px;color:#64748b;font-weight:bold;">Email:</td><td style="padding:8px;">{perfil.user.email}</td></tr>
          <tr><td style="padding:8px;color:#64748b;font-weight:bold;">Teléfono:</td><td style="padding:8px;">{perfil.telefono or 'No especificado'}</td></tr>
        </table>
        <div style="margin-top:20px;padding:16px;background:#fef3c7;border-radius:6px;border-left:4px solid #f59e0b;">
          <strong>⚠️ Acción requerida:</strong> Entra al panel de administración para aprobar o rechazar este acceso.
        </div>
        <p style="margin-top:16px;color:#64748b;font-size:13px;">Este es un mensaje automático del sistema SIB Bark.</p>
      </div>
    </div>
    """
    text = f"Nueva solicitud de acceso: {perfil.razon_social} (RUT: {perfil.rut}, Email: {perfil.user.email})"
    _send_safe(subject, text, destinatarios, html_message=html)


# ─────────────────────────────────────────────────────
# 2. Acceso aprobado → Cliente
# ─────────────────────────────────────────────────────
def email_acceso_aprobado(perfil):
    """Notifica al cliente que su acceso al portal fue aprobado."""
    subject = "✅ Tu acceso al portal de OCs ha sido aprobado"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Portal OC Clientes</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <h3 style="color:#16a34a;">¡Acceso Aprobado! 🎉</h3>
        <p>Hola <strong>{perfil.user.get_full_name() or perfil.razon_social}</strong>,</p>
        <p>Tu solicitud de acceso al <strong>Portal de Órdenes de Compra de Maestranza Bark SPA</strong> ha sido <strong>aprobada</strong>.</p>
        <p>Ya puedes iniciar sesión y comenzar a enviar tus Órdenes de Compra directamente a nuestro equipo.</p>
        <div style="margin:24px 0;text-align:center;">
          <a href="#" style="background:#2563eb;color:white;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;">Ingresar al Portal</a>
        </div>
        <p style="color:#64748b;font-size:13px;">Si tienes dudas, contáctanos a <a href="mailto:administracion@maestranzabark.cl">administracion@maestranzabark.cl</a></p>
      </div>
    </div>
    """
    text = f"Tu acceso al portal OC de Maestranza Bark SPA ha sido aprobado. Ya puedes ingresar y enviar tus OCs."
    _send_safe(subject, text, [perfil.user.email], html_message=html)


# ─────────────────────────────────────────────────────
# 3. Acceso rechazado → Cliente
# ─────────────────────────────────────────────────────
def email_acceso_rechazado(perfil):
    """Notifica al cliente que su solicitud de acceso fue rechazada."""
    subject = "❌ Solicitud de acceso al portal — Estado de tu solicitud"
    motivo = perfil.observaciones_rechazo or "No se especificó un motivo."
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Portal OC Clientes</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <h3 style="color:#dc2626;">Solicitud No Aprobada</h3>
        <p>Hola <strong>{perfil.user.get_full_name() or perfil.razon_social}</strong>,</p>
        <p>Lamentablemente, tu solicitud de acceso al portal no fue aprobada en esta ocasión.</p>
        <div style="padding:16px;background:#fef2f2;border-radius:6px;border-left:4px solid #dc2626;margin:16px 0;">
          <strong>Motivo:</strong> {motivo}
        </div>
        <p>Para más información, comunícate con nuestro equipo a <a href="mailto:administracion@maestranzabark.cl">administracion@maestranzabark.cl</a></p>
      </div>
    </div>
    """
    text = f"Tu solicitud de acceso al portal OC fue rechazada. Motivo: {motivo}"
    _send_safe(subject, text, [perfil.user.email], html_message=html)


# ─────────────────────────────────────────────────────
# 4. OC Recibida → Staff Bark
# ─────────────────────────────────────────────────────
def email_oc_recibida(oc):
    """Notifica al equipo Bark que se recibió una nueva OC de un cliente."""
    destinatarios = _get_destinatarios_internos()
    monto_str = f"${oc.monto_total:,.0f}" if oc.monto_total else "No especificado"
    subject = f"📋 Nueva OC recibida — {oc.cliente.razon_social} | N° {oc.numero_oc}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Nueva OC Recibida</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <h3 style="color:#1e293b;">OC #{oc.numero_oc} pendiente de revisión</h3>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px;color:#64748b;font-weight:bold;">Cliente:</td><td style="padding:8px;">{oc.cliente.razon_social}</td></tr>
          <tr style="background:#f1f5f9;"><td style="padding:8px;color:#64748b;font-weight:bold;">RUT:</td><td style="padding:8px;">{oc.cliente.rut}</td></tr>
          <tr><td style="padding:8px;color:#64748b;font-weight:bold;">N° OC:</td><td style="padding:8px;font-weight:bold;">{oc.numero_oc}</td></tr>
          <tr style="background:#f1f5f9;"><td style="padding:8px;color:#64748b;font-weight:bold;">Monto Total:</td><td style="padding:8px;font-size:18px;font-weight:bold;color:#16a34a;">{monto_str}</td></tr>
          <tr><td style="padding:8px;color:#64748b;font-weight:bold;">Fecha Envío:</td><td style="padding:8px;">{oc.fecha_envio.strftime('%d/%m/%Y %H:%M') if oc.fecha_envio else '-'}</td></tr>
          <tr style="background:#f1f5f9;"><td style="padding:8px;color:#64748b;font-weight:bold;">Descripción:</td><td style="padding:8px;">{oc.descripcion or '-'}</td></tr>
        </table>
        <div style="margin-top:20px;padding:16px;background:#eff6ff;border-radius:6px;border-left:4px solid #2563eb;">
          <strong>📎 Archivo adjunto:</strong> La OC fue subida en PDF al portal. Entra al panel para revisarla.
        </div>
      </div>
    </div>
    """
    text = f"Nueva OC #{oc.numero_oc} de {oc.cliente.razon_social} (RUT: {oc.cliente.rut}). Monto: {monto_str}."
    _send_safe(subject, text, destinatarios, html_message=html)


# ─────────────────────────────────────────────────────
# 5. OC Aceptada → Cliente
# ─────────────────────────────────────────────────────
def email_oc_aceptada(oc):
    """Notifica al cliente que su OC fue aceptada."""
    subject = f"✅ OC #{oc.numero_oc} — ACEPTADA por Maestranza Bark SPA"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Orden de Compra Aceptada</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <div style="text-align:center;padding:20px 0;">
          <div style="font-size:48px;">✅</div>
          <h2 style="color:#16a34a;margin:8px 0;">OC Aceptada</h2>
          <p style="font-size:24px;font-weight:bold;color:#1e293b;">N° {oc.numero_oc}</p>
        </div>
        <p>Estimado equipo de <strong>{oc.cliente.razon_social}</strong>,</p>
        <p>Nos complace informarles que hemos <strong>aceptado</strong> su Orden de Compra N° <strong>{oc.numero_oc}</strong>. Procederemos con el proceso correspondiente.</p>
        <div style="padding:16px;background:#f0fdf4;border-radius:6px;border-left:4px solid #16a34a;margin:16px 0;">
          Nuestro equipo se pondrá en contacto para coordinar los detalles del pedido.
        </div>
        <p>Atentamente,<br><strong>Equipo Maestranza Bark SPA</strong><br>
        📧 administracion@maestranzabark.cl | 📞 +56 9 4016 0112</p>
      </div>
    </div>
    """
    text = f"Su OC #{oc.numero_oc} ha sido ACEPTADA por Maestranza Bark SPA. Procederemos con el proceso."
    _send_safe(subject, text, [oc.cliente.user.email], html_message=html)


# ─────────────────────────────────────────────────────
# 6. OC Rechazada → Cliente
# ─────────────────────────────────────────────────────
def email_oc_rechazada(oc):
    """Notifica al cliente que su OC fue rechazada con el motivo."""
    subject = f"❌ OC #{oc.numero_oc} — No podemos procesar tu solicitud"
    motivo = oc.observaciones_bark or "No se especificó un motivo."
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Orden de Compra</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <h3 style="color:#dc2626;">OC #{oc.numero_oc} — No Procesada</h3>
        <p>Estimado equipo de <strong>{oc.cliente.razon_social}</strong>,</p>
        <p>Lamentablemente, no hemos podido procesar su Orden de Compra N° <strong>{oc.numero_oc}</strong>.</p>
        <div style="padding:16px;background:#fef2f2;border-radius:6px;border-left:4px solid #dc2626;margin:16px 0;">
          <strong>Observaciones:</strong><br>{motivo}
        </div>
        <p>Si tiene preguntas, no dude en contactarnos para buscar una solución.</p>
        <p>Atentamente,<br><strong>Equipo Maestranza Bark SPA</strong><br>
        📧 administracion@maestranzabark.cl | 📞 +56 9 4016 0112</p>
      </div>
    </div>
    """
    text = f"Su OC #{oc.numero_oc} no pudo ser procesada. Observaciones: {motivo}"
    _send_safe(subject, text, [oc.cliente.user.email], html_message=html)


# ─────────────────────────────────────────────────────
# 7. Solicitudes de Registro de Staff (Empleados Bark)
# ─────────────────────────────────────────────────────
def email_staff_acceso_pendiente(user):
    """Notifica al empleado (staff) que su cuenta está esperando aprobación."""
    subject = "⏳ Cuenta en estado de espera — Maestranza Bark"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Sistema Interno</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <h3 style="color:#f59e0b;">Solicitud Recibida</h3>
        <p>Hola <strong>{user.first_name or user.username}</strong>,</p>
        <p>Tu cuenta de empleado en SIB Bark ha sido creada y actualmente se encuentra en <strong>estado de espera</strong>.</p>
        <div style="padding:16px;background:#fef3c7;border-radius:6px;border-left:4px solid #f59e0b;margin:16px 0;">
          El administrador debe revisar y aprobar tu cuenta para que puedas iniciar sesión. Te notificaremos cuando esto ocurra.
        </div>
        <p>¡Gracias!<br><strong>Equipo Maestranza Bark SPA</strong></p>
      </div>
    </div>
    """
    text = "Tu cuenta de empleado en SIB Bark se encuentra en estado de espera para ser aprobada."
    _send_safe(subject, text, [user.email], html_message=html)

def email_nueva_solicitud_staff(user):
    """Notifica a los responsables que hay un nuevo empleado esperando aprobación."""
    destinatarios = _get_destinatarios_internos()
    subject = f"🆕 Nuevo empleado registrado — {user.first_name}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Sistema Interno</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <h3 style="color:#1e293b;">Nueva solicitud de Empleado 💼</h3>
        <p>El siguiente usuario se acaba de registrar en el panel de empleados:</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr><td style="padding:8px;color:#64748b;font-weight:bold;">Nombre:</td><td style="padding:8px;">{user.first_name}</td></tr>
          <tr style="background:#f1f5f9;"><td style="padding:8px;color:#64748b;font-weight:bold;">Usuario (Login):</td><td style="padding:8px;">{user.username}</td></tr>
          <tr><td style="padding:8px;color:#64748b;font-weight:bold;">Email:</td><td style="padding:8px;">{user.email}</td></tr>
        </table>
        <div style="padding:16px;background:#eff6ff;border-radius:6px;border-left:4px solid #3b82f6;">
          <strong>Acción requerida:</strong> Ingresa al panel de Accesos para activar esta cuenta.
        </div>
      </div>
    </div>
    """
    text = f"Nuevo registro de empleado: {user.first_name} (Usuario: {user.username}). Ve al panel de Accesos para aprobarlo."
    _send_safe(subject, text, destinatarios, html_message=html)

def email_staff_acceso_aprobado(user):
    """Notifica al empleado que su cuenta ya fue activada."""
    subject = "✅ Tu cuenta en Bark ha sido activada"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="color:#60a5fa;margin:0;">SIB Bark — Sistema Interno</h2>
      </div>
      <div style="background:#f8fafc;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <h3 style="color:#16a34a;">¡Cuenta Activada! 🎉</h3>
        <p>Hola <strong>{user.first_name or user.username}</strong>,</p>
        <p>Tu cuenta de empleado ha sido <strong>aprobada y activada</strong> por el administrador.</p>
        <p>Ya puedes iniciar sesión en el panel interno usando tus credenciales.</p>
        <div style="margin:24px 0;text-align:center;">
          <a href="#" style="background:#2563eb;color:white;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;">Ingresar al Sistema</a>
        </div>
      </div>
    </div>
    """
    text = "Tu cuenta de empleado en Maestranza Bark SPA ha sido activada. Ya puedes iniciar sesión."
    _send_safe(subject, text, [user.email], html_message=html)

