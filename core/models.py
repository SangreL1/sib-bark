from decimal import Decimal
from django.db import models
from django.utils import timezone


class OrdenCompra(models.Model):
    PRIORIDADES = [
        ('URGENTE', '🔴 Urgente'),
        ('ALTA', '🟠 Alta'),
        ('NORMAL', '🟡 Normal'),
        ('BAJA', '🟢 Baja'),
    ]

    ESTADOS = [
        ('En proceso', 'En proceso'),
        ('Facturado', 'Facturado'),
        ('Cerrado', 'Cerrado'),
        ('Pendiente', 'Pendiente'),
        ('Cancelado', 'Cancelado'),
    ]

    numero_oc = models.CharField(max_length=255, primary_key=True, verbose_name="Número OC")
    cliente = models.CharField(max_length=255, verbose_name="Cliente")
    fecha_oc = models.DateField(null=True, blank=True, verbose_name="Fecha OC")
    proyecto = models.CharField(max_length=255, null=True, blank=True, verbose_name="Proyecto")
    descripcion = models.TextField(null=True, blank=True, verbose_name="Descripción")

    # Financials
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Valor Total SIN IVA")

    # Manufacturing timeline
    tiempo_fabricacion = models.IntegerField(null=True, blank=True, verbose_name="Tiempo fabricación (días háb.)")
    fecha_compromiso = models.DateField(null=True, blank=True, verbose_name="Fecha Compromiso")
    estado = models.CharField(max_length=100, choices=ESTADOS, default='En proceso', verbose_name="Estado")
    porcentaje_entregado = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="% Entregado")
    fecha_ultima_entrega = models.DateField(null=True, blank=True, verbose_name="Fecha Última Entrega")
    dias_restantes = models.IntegerField(null=True, blank=True, verbose_name="Días Restantes")
    prioridad = models.CharField(max_length=100, choices=PRIORIDADES, null=True, blank=True, verbose_name="Prioridad")

    # Summaries
    guia_despacho_resumen = models.CharField(max_length=255, null=True, blank=True, verbose_name="Guía de Despacho")
    factura_resumen = models.CharField(max_length=255, null=True, blank=True, verbose_name="Factura")
    fecha_factura = models.DateField(null=True, blank=True, verbose_name="Fecha Factura")
    observaciones = models.TextField(null=True, blank=True, verbose_name="Observaciones")

    # Document links (Google Drive or other)
    oc_link = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Link OC (PDF)")
    fmr_link = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Link FMR (PDF)")
    plano_link = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Link Planos")
    excel_link = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Link Excel")
    dossier_link = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Link Dossier Calidad")
    cotizacion_link = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Link Cotización")

    # Physical file uploads (in addition to links, satisfying user request)
    oc_file = models.FileField(upload_to='ordenes_compra/oc/', blank=True, null=True, verbose_name="Archivo OC (PDF)")
    fmr_file = models.FileField(upload_to='ordenes_compra/fmr/', blank=True, null=True, verbose_name="Archivo FMR (PDF)")
    plano_file = models.FileField(upload_to='ordenes_compra/planos/', blank=True, null=True, verbose_name="Archivo Planos")
    excel_file = models.FileField(upload_to='ordenes_compra/excel/', blank=True, null=True, verbose_name="Archivo Excel")
    dossier_file = models.FileField(upload_to='ordenes_compra/dossiers/', blank=True, null=True, verbose_name="Archivo Dossier")
    cotizacion_file = models.FileField(upload_to='ordenes_compra/cotizaciones/', blank=True, null=True, verbose_name="Archivo Cotización")

    # Audit
    creado_en = models.DateTimeField(auto_now_add=True, null=True)
    actualizado_en = models.DateTimeField(auto_now=True, null=True)

    # ------------------------------------------------------------------ #
    #  SEMÁFOROS — Calculados automáticamente, no almacenados en DB       #
    # ------------------------------------------------------------------ #

    @property
    def semaforo_plazo(self):
        """
        🟢 verde  → días_restantes > 5
        🟡 amarillo → 0 < días_restantes <= 5
        🔴 rojo   → atrasado o estado final
        """
        if self.estado in ('Facturado', 'Cerrado', 'Cancelado'):
            return 'grey'
        if self.fecha_compromiso:
            delta = (self.fecha_compromiso - timezone.now().date()).days
            if delta > 5:
                return 'green'
            elif delta > 0:
                return 'yellow'
            else:
                return 'red'
        return 'grey'

    @property
    def semaforo_avance(self):
        """
        🟢 verde  → 100% o estado Facturado/Cerrado (implica entrega completa)
        🟡 amarillo → 50–99%
        🔴 rojo   → < 50%
        """
        if self.estado in ('Facturado', 'Cerrado'):
            return 'green'
        pct = float(self.porcentaje_entregado or 0)
        if pct >= 100:
            return 'green'
        elif pct >= 50:
            return 'yellow'
        else:
            return 'red'

    @property
    def semaforo_docs(self):
        """
        🟢 verde  → tiene OC + Plano + al menos 1 FMR (link o archivo)
        🟡 amarillo → tiene OC o Plano (link o archivo)
        🔴 rojo   → sin ningún documento
        """
        has_oc = bool(self.oc_link or self.oc_file)
        has_plano = bool(self.plano_link or self.plano_file)
        has_fmr_inst = self.fmrs.filter(
            models.Q(registro_link__isnull=False) | models.Q(registro_file__isnull=False)
        ).exclude(registro_link='', registro_file='').exists()
        
        has_fmr = has_fmr_inst or bool(self.fmr_link or self.fmr_file)

        if has_oc and has_plano and has_fmr:
            return 'green'
        elif has_oc or has_plano:
            return 'yellow'
        return 'red'

    @property
    def dias_restantes_calculado(self):
        if self.fecha_compromiso:
            return (self.fecha_compromiso - timezone.now().date()).days
        return None

    @property
    def margen(self):
        """Margen bruto = valor_total − suma de todos los costos de esta OC."""
        if not self.valor_total:
            return Decimal('0.00')
        total_costos = self.costos.aggregate(total=models.Sum('monto'))['total'] or Decimal('0.00')
        return self.valor_total - total_costos

    @property
    def margen_porcentaje(self):
        """% de margen sobre el valor total de la OC."""
        if not self.valor_total or self.valor_total == 0:
            return Decimal('0.00')
        return round((self.margen / self.valor_total) * 100, 2)

    @property
    def costo_total_mano_obra(self):
        return self.manos_de_obra.aggregate(total=models.Sum('total'))['total'] or Decimal('0.00')

    @property
    def costo_total_materiales(self):
        return self.materias_primas.aggregate(total=models.Sum('total'))['total'] or Decimal('0.00')

    @property
    def costo_total_trabajo(self):
        return self.costo_total_mano_obra + self.costo_total_materiales

    @property
    def peso_total_kg(self):
        return self.items.aggregate(total=models.Sum('peso'))['total'] or Decimal('0.00')

    @property
    def utilidad_real(self):
        valor = self.valor_total or Decimal('0.00')
        return valor - self.costo_total_trabajo

    @property
    def costo_por_kilo(self):
        peso = self.peso_total_kg
        if peso > 0:
            return self.costo_total_trabajo / peso
        return Decimal('0.00')

    @property
    def utilidad_por_kilo(self):
        peso = self.peso_total_kg
        if peso > 0:
            return self.utilidad_real / peso
        return Decimal('0.00')

    @property
    def porcentaje_utilidad(self):
        valor = self.valor_total or Decimal('0.00')
        if valor > 0:
            return (self.utilidad_real / valor) * 100
        return Decimal('0.00')


    def recalcular_porcentaje(self):
        """Recalculates % delivered based on ItemOC counts where available, otherwise falls back to Entrega records."""
        items = self.items.all()
        if items.exists():
            total_qty = sum(item.cantidad for item in items)
            if total_qty == 0:
                self.porcentaje_entregado = 0
            else:
                delivered_qty = sum(item.cantidad_entregada for item in items)
                self.porcentaje_entregado = min(round((delivered_qty / total_qty) * 100, 2), 100)
        else:
            entregas = self.entregas.all()
            total = entregas.count()
            if total == 0:
                self.porcentaje_entregado = 0
            else:
                completas = entregas.filter(estado__icontains='COMPLETA').count()
                self.porcentaje_entregado = min(round((completas / total) * 100, 2), 100)
        self.save(update_fields=['porcentaje_entregado'])

    def __str__(self):
        return f"{self.numero_oc} — {self.cliente}"

    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha_oc']


class FMR(models.Model):
    fmr_code = models.CharField(max_length=100, unique=True, verbose_name="Código FMR")
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='fmrs',
        verbose_name="Orden de Compra"
    )
    fecha = models.DateField(null=True, blank=True, verbose_name="Fecha")
    cotizacion = models.CharField(max_length=100, null=True, blank=True, verbose_name="N° Cotización")
    guia_despacho = models.CharField(max_length=255, null=True, blank=True, verbose_name="Guía Despacho")
    factura = models.CharField(max_length=100, null=True, blank=True, verbose_name="N° Factura")
    registro_link = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Link Registro Final (PDF)")
    registro_file = models.FileField(upload_to='fmr/registros/', blank=True, null=True, verbose_name="Archivo Registro Final (PDF)")

    def __str__(self):
        return f"FMR {self.fmr_code}"

    class Meta:
        verbose_name = "FMR"
        verbose_name_plural = "FMRs"
        ordering = ['-fmr_code']


class Entrega(models.Model):
    ESTADOS_ENTREGA = [
        ('COMPLETA', 'Entrega Completa'),
        ('INCOMPLETA', 'Entrega Incompleta'),
        ('FACTURADO', 'Facturado'),
    ]

    ESTADOS_FACTURACION = [
        ('facturado', 'Facturado'),
        ('por_facturar', 'Por facturar'),
    ]

    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='entregas', verbose_name="Orden de Compra"
    )
    fecha_entrega = models.DateField(null=True, blank=True, verbose_name="Fecha Entrega")
    guia_despacho = models.CharField(max_length=100, null=True, blank=True, verbose_name="N° Guía de Despacho")
    guia_file = models.FileField(upload_to='entregas/guias/', blank=True, null=True, verbose_name="Archivo Guía de Despacho")
    cantidad_entregada = models.TextField(null=True, blank=True, verbose_name="Detalle / Cantidad Entregada")
    observaciones = models.TextField(null=True, blank=True, verbose_name="Observaciones")
    estado = models.CharField(
        max_length=100, choices=ESTADOS_ENTREGA,
        default='COMPLETA', verbose_name="Estado"
    )
    estado_facturacion = models.CharField(
        max_length=50, choices=ESTADOS_FACTURACION,
        default='por_facturar', verbose_name="Estado de Facturación"
    )


    def __str__(self):
        return f"Guía {self.guia_despacho} — {self.orden_compra.numero_oc}"

    class Meta:
        verbose_name = "Entrega Parcial"
        verbose_name_plural = "Entregas Parciales"
        ordering = ['-fecha_entrega']


class Costo(models.Model):
    CATEGORIAS = [
        ('Materiales', 'Materiales'),
        ('Mano de Obra', 'Mano de Obra'),
        ('Subcontratos', 'Subcontratos'),
        ('Transporte', 'Transporte'),
        ('Otros', 'Otros'),
    ]

    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='costos', verbose_name="Orden de Compra"
    )
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, verbose_name="Categoría")
    descripcion = models.CharField(max_length=255, verbose_name="Descripción / Detalle")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto ($)")
    proveedor = models.CharField(max_length=255, blank=True, null=True, verbose_name="Proveedor / Empleado")
    fecha = models.DateField(verbose_name="Fecha del Gasto")
    documento_referencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Doc. Referencia")

    def __str__(self):
        return f"{self.categoria}: ${self.monto} — OC {self.orden_compra.numero_oc}"

    class Meta:
        verbose_name = "Registro de Costo"
        verbose_name_plural = "Registros de Costos"
        ordering = ['-fecha']


class Trazabilidad(models.Model):
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='trazabilidades', verbose_name="Orden de Compra"
    )
    usuario = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Usuario"
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")
    accion = models.CharField(max_length=255, verbose_name="Acción Realizada")
    detalle = models.TextField(blank=True, null=True, verbose_name="Detalles de la Acción")

    class Meta:
        verbose_name = "Registro de Trazabilidad"
        verbose_name_plural = "Registros de Trazabilidad"
        ordering = ['-fecha_hora']


class ItemOC(models.Model):
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='items', verbose_name="Orden de Compra"
    )
    linea = models.CharField(max_length=50, verbose_name="Línea / Item")
    codigo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Item (Size/Code)")
    descripcion = models.CharField(max_length=255, verbose_name="Descripción")
    unidad = models.CharField(max_length=20, default='EA', verbose_name="Unidad de Medida (UOM)")
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=1.0, verbose_name="Cantidad")
    peso_unitario_kg = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Peso Unitario (kg)")
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Precio Unitario")
    cantidad_entregada = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Cantidad Entregada")

    # Nuevos campos del BOM real
    item_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="Item Code")
    size_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="Size Code")
    uom = models.CharField(max_length=100, blank=True, null=True, verbose_name="UOM")
    precio_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Precio Total")
    fecha_entrega = models.DateField(blank=True, null=True, verbose_name="Fecha de Entrega")
    peso = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Peso (kg)")

    @property
    def valor_total(self):
        return self.cantidad * self.precio_unitario

    @property
    def peso_total_kg(self):
        if self.peso_unitario_kg:
            return self.cantidad * self.peso_unitario_kg
        return 0.00

    def __str__(self):
        return f"{self.linea} - {self.descripcion} ({self.codigo or ''})"

    def save(self, *args, **kwargs):
        if self.cantidad is not None and self.precio_unitario is not None:
            self.precio_total = Decimal(self.cantidad) * Decimal(self.precio_unitario)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Item de Orden de Compra"
        verbose_name_plural = "Items de Orden de Compra"
        ordering = ['linea']


class PackingListItem(models.Model):
    entrega = models.ForeignKey(
        Entrega, on_delete=models.CASCADE,
        related_name='packing_list_items', verbose_name="Entrega / Despacho"
    )
    item_oc = models.ForeignKey(
        ItemOC, on_delete=models.CASCADE,
        related_name='packing_items', verbose_name="Ítem de la OC"
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=1.0, verbose_name="Cantidad Despachada")

    # Dimensiones y Peso de la entrega física
    numero_bulto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Pallet / Bulto N°")
    largo_mt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Largo (mt)")
    ancho_mt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Ancho (mt)")
    alto_mt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Alto (mt)")
    peso_kg = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Peso (kg)")

    # Campos custom para el reporte de calidad / Packing List del cliente
    modelo_soporte = models.CharField(max_length=255, blank=True, null=True, verbose_name="Modelo Soporte")
    # Campos legacy (se mantienen para no romper datos existentes)
    diametro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Diámetro / Ø")
    alto_item = models.CharField(max_length=100, blank=True, null=True, verbose_name="Alto Item")
    estado_item = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estado de Item")
    unidades = models.CharField(max_length=100, blank=True, null=True, verbose_name="Unidades")
    # Campos genéricos de medida (Formato A: Ø+ALTO / Formato B: L+H)
    medida_1 = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="Medida 1 (Ø o L)")
    medida_2 = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="Medida 2 (Alto o H)")

    def __str__(self):
        return f"{self.numero_bulto or 'Bulto'} - {self.item_oc.descripcion} ({self.cantidad})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculate cantidad_entregada for the ItemOC
        item = self.item_oc
        total_delivered = item.packing_items.aggregate(total=models.Sum('cantidad'))['total'] or Decimal('0.00')
        item.cantidad_entregada = total_delivered
        item.save()
        # Recalculate porcentaje_entregado for the OrdenCompra
        item.orden_compra.recalcular_porcentaje()

    def delete(self, *args, **kwargs):
        item = self.item_oc
        super().delete(*args, **kwargs)
        # Recalculate cantidad_entregada for the ItemOC
        total_delivered = item.packing_items.aggregate(total=models.Sum('cantidad'))['total'] or Decimal('0.00')
        item.cantidad_entregada = total_delivered
        item.save()
        # Recalculate porcentaje_entregado for the OrdenCompra
        item.orden_compra.recalcular_porcentaje()

    class Meta:
        verbose_name = "Ítem de Packing List"
        verbose_name_plural = "Ítems de Packing List"


# ──────────────────────────────────────────────────────────────────────────────
# FACTURA — Modelo de facturación asociado a Entrega / OC
# ──────────────────────────────────────────────────────────────────────────────

class Factura(models.Model):
    ESTADOS_FACTURA = [
        ('pendiente', '🟡 Pendiente de pago'),
        ('pagada',    '🟢 Pagada'),
    ]

    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='facturas', verbose_name="Orden de Compra"
    )
    entrega = models.ForeignKey(
        Entrega, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='facturas', verbose_name="Entrega / Despacho asociado"
    )

    numero_factura = models.CharField(max_length=100, verbose_name="N° Factura")
    fecha_emision  = models.DateField(verbose_name="Fecha de Emisión")
    monto          = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto ($)")
    estado         = models.CharField(
        max_length=20, choices=ESTADOS_FACTURA,
        default='pendiente', verbose_name="Estado de Pago"
    )

    # Patrón dual: link externo + archivo físico (igual que el resto del sistema)
    url_externa = models.URLField(
        max_length=1000, blank=True, null=True,
        verbose_name="Link externo (Drive/SharePoint)"
    )
    archivo = models.FileField(
        upload_to='facturas/', blank=True, null=True,
        verbose_name="Archivo Factura (PDF)"
    )

    def __str__(self):
        return f"Factura {self.numero_factura} — OC {self.orden_compra_id}"

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_emision']


# ──────────────────────────────────────────────────────────────────────────────
# COSTO MATERIAL — Detalle de materiales comprados para una OC
# ──────────────────────────────────────────────────────────────────────────────

class CostoMaterial(models.Model):
    """
    Registra cada material comprado para producir la OC.
    Equivale a la hoja 'MATERIAL Y MANO DE OBRA' del Excel del cliente,
    columnas: PRODUCTO / CANTIDAD / VALOR / TOTAL.
    """
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='costos_materiales', verbose_name="Orden de Compra"
    )
    producto     = models.CharField(max_length=255, verbose_name="Producto / Material")
    cantidad     = models.DecimalField(
        max_digits=12, decimal_places=2, default=1,
        verbose_name="Cantidad"
    )
    valor_unitario = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="Valor Unitario ($)"
    )
    proveedor    = models.CharField(max_length=255, blank=True, null=True, verbose_name="Proveedor")
    fecha_compra = models.DateField(null=True, blank=True, verbose_name="Fecha de Compra")
    observaciones = models.CharField(max_length=500, blank=True, null=True, verbose_name="Observaciones")

    @property
    def total(self):
        """Costo total = cantidad × valor_unitario."""
        return self.cantidad * self.valor_unitario

    def __str__(self):
        return f"{self.producto} × {self.cantidad} — OC {self.orden_compra_id}"

    class Meta:
        verbose_name = "Material Comprado"
        verbose_name_plural = "Materiales Comprados"
        ordering = ['producto']


# ──────────────────────────────────────────────────────────────────────────────
# COSTO MANO DE OBRA — Detalle por cargo/rol para una OC
# ──────────────────────────────────────────────────────────────────────────────

class CostoManoObra(models.Model):
    """
    Registra el costo real de mano de obra por rol para la OC.
    Basado en la hoja 'MATERIAL Y MANO DE OBRA' del cliente:
    Cargo / Horas / Sueldo por hora / Cantidad trabajadores / Horas extra.
    """
    CARGOS_PREDEFINIDOS = [
        ('Ayudante',          'Ayudante'),
        ('Ayudante mayor',    'Ayudante mayor'),
        ('Maestro',           'Maestro'),
        ('Maestro mayor',     'Maestro mayor'),
        ('Pintor',            'Pintor'),
        ('Adquisiciones',     'Adquisiciones'),
        ('Jefe Operaciones',  'Jefe de Operaciones'),
        ('Gerente',           'Gerente'),
        ('Otro',              'Otro (especificar)'),
    ]

    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='costos_mano_obra', verbose_name="Orden de Compra"
    )
    cargo               = models.CharField(max_length=100, choices=CARGOS_PREDEFINIDOS, verbose_name="Cargo / Rol")
    cargo_otro          = models.CharField(max_length=100, blank=True, null=True, verbose_name="Especificar cargo (si 'Otro')")
    precio_hora         = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio por hora ($)")
    horas_normales      = models.DecimalField(max_digits=8, decimal_places=1, default=0, verbose_name="Horas normales")
    horas_extra         = models.DecimalField(max_digits=8, decimal_places=1, default=0, verbose_name="Horas extra")
    cantidad_trabajadores = models.IntegerField(default=1, verbose_name="Cantidad de trabajadores")

    @property
    def horas_totales(self):
        return self.horas_normales + self.horas_extra

    @property
    def costo_base(self):
        """Costo de horas normales × precio × cantidad trabajadores."""
        return self.horas_normales * self.precio_hora * self.cantidad_trabajadores

    @property
    def costo_extra(self):
        """Costo de horas extra × precio × cantidad trabajadores."""
        return self.horas_extra * self.precio_hora * self.cantidad_trabajadores

    @property
    def total(self):
        """Costo total = (horas normales + horas extra) × precio_hora × cantidad."""
        return self.horas_totales * self.precio_hora * self.cantidad_trabajadores

    @property
    def nombre_cargo(self):
        return self.cargo_otro if self.cargo == 'Otro' and self.cargo_otro else self.cargo

    def __str__(self):
        return f"{self.nombre_cargo} × {self.cantidad_trabajadores} — OC {self.orden_compra_id}"

    class Meta:
        verbose_name = "Costo de Mano de Obra"
        verbose_name_plural = "Costos de Mano de Obra"
        ordering = ['cargo']


class Cargo(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Cargo")
    precio_hora = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio por Hora ($)")

    def __str__(self):
        return f"{self.nombre} (${self.precio_hora}/hr)"

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['nombre']


class ManoDeObra(models.Model):
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='manos_de_obra', verbose_name="Orden de Compra"
    )
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, verbose_name="Cargo")
    dias = models.IntegerField(verbose_name="Días")
    horas = models.IntegerField(verbose_name="Horas")
    cantidad_trabajadores = models.IntegerField(verbose_name="Cantidad de Trabajadores")
    horas_extra = models.IntegerField(default=0, verbose_name="Horas Extra")

    # Campos calculados persistidos en BD
    costo_por_trabajador = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Costo por Trabajador")
    mano_obra_base = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Mano de Obra Base")
    costo_horas_extra = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Costo Horas Extra")
    total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Total ($)")

    def save(self, *args, **kwargs):
        # Fórmulas solicitadas:
        # costo_por_trabajador = cargo.precio_hora * dias * horas
        # mano_obra_base = costo_por_trabajador * cantidad_trabajadores
        # costo_horas_extra = horas_extra * cargo.precio_hora
        # total = mano_obra_base + costo_horas_extra
        precio = self.cargo.precio_hora
        self.costo_por_trabajador = Decimal(precio) * Decimal(self.dias) * Decimal(self.horas)
        self.mano_obra_base = Decimal(self.costo_por_trabajador) * Decimal(self.cantidad_trabajadores)
        self.costo_horas_extra = Decimal(self.horas_extra) * Decimal(precio)
        self.total = Decimal(self.mano_obra_base) + Decimal(self.costo_horas_extra)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MO: {self.cargo.nombre} × {self.cantidad_trabajadores} — OC {self.orden_compra.numero_oc}"

    class Meta:
        verbose_name = "Mano de Obra (Detallada)"
        verbose_name_plural = "Mano de Obra (Detallada)"


class MateriaPrima(models.Model):
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='materias_primas', verbose_name="Orden de Compra"
    )
    producto = models.CharField(max_length=255, verbose_name="Producto / Detalle")
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Cantidad")
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Unitario ($)")
    total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Total ($)")

    def save(self, *args, **kwargs):
        if self.cantidad is not None:
            self.total = Decimal(self.cantidad) * Decimal(self.valor_unitario)
        # Si la cantidad no existe, total se ingresa directamente y se conserva
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MP: {self.producto} — OC {self.orden_compra.numero_oc}"

    class Meta:
        verbose_name = "Materia Prima (Detallada)"
        verbose_name_plural = "Materias Primas (Detalladas)"


class PackingList(models.Model):
    TIPO_MEDIDA_CHOICES = [
        ('diametro_alto', 'Ø / Alto'),
        ('largo_alto', 'L / H'),
    ]

    numero_correlativo = models.IntegerField(unique=True, null=True, blank=True, verbose_name="Número Correlativo")
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE,
        related_name='packing_lists', verbose_name="Orden de Compra"
    )
    entrega = models.ForeignKey(
        Entrega, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='packing_lists', verbose_name="Despacho / Entrega"
    )
    fecha_orden = models.DateField(verbose_name="Fecha de Orden")
    fecha_envio = models.DateField(verbose_name="Fecha de Envío")
    nombre_cliente = models.CharField(max_length=255, verbose_name="Nombre del Cliente")
    empresa = models.CharField(max_length=255, default="MAESTRANZA BARK SPA", verbose_name="Empresa")
    direccion = models.CharField(max_length=255, default="Camino F-30-E N° 1200, Quintero, Valparaíso", verbose_name="Dirección")
    correo = models.CharField(max_length=255, default="contacto@maestranzabark.cl", verbose_name="Correo")
    telefono = models.CharField(max_length=255, default="+56 9 1234 5678", verbose_name="Teléfono")
    tipo_medida = models.CharField(
        max_length=20,
        choices=TIPO_MEDIDA_CHOICES,
        default='diametro_alto',
        verbose_name="Formato de Columnas"
    )

    @property
    def col_medida_1(self):
        return 'Ø' if self.tipo_medida == 'diametro_alto' else 'L'

    @property
    def col_medida_2(self):
        return 'ALTO' if self.tipo_medida == 'diametro_alto' else 'H'

    def save(self, *args, **kwargs):
        if not self.numero_correlativo:
            from django.db import transaction
            with transaction.atomic():
                max_val = PackingList.objects.select_for_update().aggregate(max_val=models.Max('numero_correlativo'))['max_val']
                self.numero_correlativo = (max_val or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Packing List N° {self.numero_correlativo} — OC {self.orden_compra_id}"

    class Meta:
        verbose_name = "Packing List"
        verbose_name_plural = "Packing Lists"
        ordering = ['-numero_correlativo']


# ──────────────────────────────────────────────────────────────────────────────
# COTIZACIÓN — Documento de presupuesto previo a la OC
# ──────────────────────────────────────────────────────────────────────────────

class Cotizacion(models.Model):
    numero_cotizacion = models.IntegerField(unique=True, null=True, blank=True, verbose_name="N° Cotización")
    fecha = models.DateField(verbose_name="Fecha")
    valido_hasta = models.DateField(null=True, blank=True, verbose_name="Válido hasta")
    cliente_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cliente ID")
    contacto_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Contacto")
    contacto_cargo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Cargo Contacto")
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cotizaciones', verbose_name="Orden de Compra"
    )
    # Datos del receptor (Razón Social cliente, para PDF)
    razon_social = models.CharField(max_length=255, blank=True, null=True, verbose_name="Razón Social")
    giro = models.CharField(max_length=255, blank=True, null=True, verbose_name="Giro")
    rut_receptor = models.CharField(max_length=20, blank=True, null=True, verbose_name="RUT")
    direccion_receptor = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    ciudad_receptor = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones / Notas")

    def save(self, *args, **kwargs):
        if not self.numero_cotizacion:
            from django.db import transaction
            with transaction.atomic():
                max_val = Cotizacion.objects.select_for_update().aggregate(max_val=models.Max('numero_cotizacion'))['max_val']
                self.numero_cotizacion = (max_val or 0) + 1
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return sum(item.valor for item in self.items.all())

    @property
    def iva(self):
        return self.subtotal * Decimal('0.19')

    @property
    def total(self):
        return self.subtotal + self.iva

    def __str__(self):
        return f"Cotización N° {self.numero_cotizacion}"

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-numero_cotizacion']


class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion, on_delete=models.CASCADE,
        related_name='items', verbose_name="Cotización"
    )
    descripcion = models.CharField(max_length=500, verbose_name="Descripción")
    observacion = models.TextField(blank=True, null=True, verbose_name="Observación / Detalle")
    valor_kg = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor por kg ($)")
    cantidad = models.IntegerField(default=1, verbose_name="Cantidad")
    kg_por_unidad = models.DecimalField(max_digits=12, decimal_places=3, default=0, verbose_name="kg por Unidad")

    @property
    def kg_total(self):
        return Decimal(str(self.cantidad)) * self.kg_por_unidad

    @property
    def valor(self):
        return self.valor_kg * self.kg_total

    def __str__(self):
        return f"{self.descripcion} — Cot. {self.cotizacion_id}"

    class Meta:
        verbose_name = "Ítem de Cotización"
        verbose_name_plural = "Ítems de Cotización"


# ──────────────────────────────────────────────────────────────────────────────
# GUÍA DE DESPACHO — Modelo estructurado (reemplaza campo de texto 'guia_despacho')
# ──────────────────────────────────────────────────────────────────────────────

class GuiaDespacho(models.Model):
    numero_guia = models.CharField(max_length=50, unique=True, verbose_name="N° Guía de Despacho")
    entrega = models.OneToOneField(
        Entrega, on_delete=models.CASCADE,
        related_name='guia_despacho_obj', verbose_name="Entrega / Despacho"
    )
    fecha_emision = models.DateField(verbose_name="Fecha de Emisión")

    # Datos del receptor
    receptor_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Razón Social Receptor")
    receptor_rut = models.CharField(max_length=20, blank=True, null=True, verbose_name="RUT Receptor")
    receptor_giro = models.CharField(max_length=255, blank=True, null=True, verbose_name="Giro Receptor")
    receptor_direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección Receptor")
    receptor_comuna = models.CharField(max_length=100, blank=True, null=True, verbose_name="Comuna Receptor")
    contacto = models.CharField(max_length=255, blank=True, null=True, verbose_name="Contacto / Persona que Recibe")

    # Datos de transporte
    tipo_despacho = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo de Despacho")
    tipo_traslado = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo de Traslado")
    chofer_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Chofer")
    chofer_rut = models.CharField(max_length=20, blank=True, null=True, verbose_name="RUT Chofer")
    patente = models.CharField(max_length=20, blank=True, null=True, verbose_name="Patente")
    transportista_rut = models.CharField(max_length=20, blank=True, null=True, verbose_name="RUT Transportista")
    direccion_destino = models.CharField(max_length=400, blank=True, null=True, verbose_name="Dirección de Destino")

    @property
    def monto_neto(self):
        return sum(item.total for item in self.items_guia.all())

    @property
    def iva(self):
        return self.monto_neto * Decimal('0.19')

    @property
    def monto_total(self):
        return self.monto_neto + self.iva

    def __str__(self):
        return f"Guía N° {self.numero_guia}"

    class Meta:
        verbose_name = "Guía de Despacho"
        verbose_name_plural = "Guías de Despacho"
        ordering = ['-fecha_emision']


class ItemGuia(models.Model):
    guia = models.ForeignKey(
        GuiaDespacho, on_delete=models.CASCADE,
        related_name='items_guia', verbose_name="Guía de Despacho"
    )
    descripcion = models.CharField(max_length=500, verbose_name="Descripción")
    cantidad_unidad = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cantidad / Unidad")
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Precio Unitario ($)")

    @property
    def total(self):
        try:
            qty = Decimal(str(self.cantidad_unidad).split()[0])
        except Exception:
            qty = Decimal('1')
        return self.precio_unitario * qty

    def __str__(self):
        return f"{self.descripcion} — Guía {self.guia_id}"

    class Meta:
        verbose_name = "Ítem de Guía"
        verbose_name_plural = "Ítems de Guía"
