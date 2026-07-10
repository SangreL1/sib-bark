from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import re
from datetime import date

def validate_rut(value):
    rut = str(value).upper().replace("-", "").replace(".", "")
    if len(rut) < 2:
        raise ValidationError("RUT demasiado corto.")
    aux = rut[:-1]
    dv = rut[-1:]
    revertido = map(int, reversed(str(aux)))
    factors = [2, 3, 4, 5, 6, 7, 2, 3, 4, 5, 6, 7]
    s = sum(d * f for d, f in zip(revertido, factors))
    res = 11 - (s % 11)
    if res == 11:
        dv_calc = "0"
    elif res == 10:
        dv_calc = "K"
    else:
        dv_calc = str(res)
    if dv != dv_calc:
        raise ValidationError("Dígito verificador inválido.")


class AFP(models.Model):
    nombre = models.CharField(max_length=100)
    comision_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Ej: 10.69 para indicar 10.69% (verificar antes de usar en producción)"
    )
    vigente_desde = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.nombre} ({self.comision_porcentaje}%)"
    
    class Meta:
        verbose_name = "AFP"
        verbose_name_plural = "AFPs"


class Empleado(models.Model):
    TIPO_CONTRATO_CHOICES = [
        ('Indefinido', 'Indefinido'),
        ('Plazo Fijo', 'Plazo Fijo'),
        ('Por Obra/Faena', 'Por Obra/Faena'),
    ]
    SISTEMA_SALUD_CHOICES = [
        ('Fonasa', 'Fonasa'),
        ('Isapre', 'Isapre'),
    ]

    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    rut = models.CharField(max_length=12, validators=[validate_rut], unique=True, help_text="Formato: 12345678-K")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    
    cargo = models.CharField(max_length=150, verbose_name="Cargo")
    tipo_contrato = models.CharField(max_length=50, choices=TIPO_CONTRATO_CHOICES, verbose_name="Tipo de Contrato")
    fecha_ingreso = models.DateField(verbose_name="Fecha de Ingreso", null=True, blank=True)
    fecha_termino = models.DateField(verbose_name="Fecha de Término", null=True, blank=True)
    unidad_negocio = models.CharField(max_length=150, verbose_name="Unidad de Negocio")
    
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Sueldo Base ($)")
    
    afp = models.ForeignKey(AFP, on_delete=models.PROTECT, verbose_name="AFP")
    sistema_salud = models.CharField(max_length=50, choices=SISTEMA_SALUD_CHOICES, verbose_name="Sistema de Salud")
    isapre_nombre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre Isapre")
    isapre_plan_uf = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Plan Isapre (UF)")
    
    cuenta_bancaria = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cuenta Bancaria")
    banco = models.CharField(max_length=100, blank=True, null=True, verbose_name="Banco")
    
    activo = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self):
        return f"{self.nombre_completo} - {self.rut}"
    
    class Meta:
        ordering = ['nombre_completo']


class Asistencia(models.Model):
    TIPO_ASISTENCIA_CHOICES = [
        ('Presente', 'Presente'),
        ('Falta Justificada', 'Falta Justificada'),
        ('Falta Injustificada', 'Falta Injustificada'),
        ('Licencia Médica', 'Licencia Médica'),
        ('Vacaciones', 'Vacaciones'),
        ('Feriado', 'Feriado'),
    ]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    tipo = models.CharField(max_length=50, choices=TIPO_ASISTENCIA_CHOICES, default='Presente')
    horas_trabajadas = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    horas_extra = models.DecimalField(max_digits=4, decimal_places=1, default=0)

    class Meta:
        unique_together = ('empleado', 'fecha')
        ordering = ['-fecha']


class TablaImpuestoUnico(models.Model):
    mes_vigencia = models.DateField(help_text="Primer día del mes (ej. 01/08/2026)")
    valor_utm = models.DecimalField(max_digits=10, decimal_places=2, help_text="Valor UTM vigente (verificar en sii.cl antes del cierre)")
    
    tramo_desde_utm = models.DecimalField(max_digits=8, decimal_places=2)
    tramo_hasta_utm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    factor = models.DecimalField(max_digits=5, decimal_places=3)
    rebaja = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto de rebaja en pesos")

    def __str__(self):
        return f"Impuesto {self.mes_vigencia.strftime('%m/%Y')} - Tramo {self.tramo_desde_utm} a {self.tramo_hasta_utm or 'Más'}"


class ParametroLegal(models.Model):
    nombre = models.CharField(max_length=100)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True, help_text="Si aplica porcentaje. Ej: 7 para 7%")
    valor_moneda = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Si aplica valor fijo o UF")
    vigente_desde = models.DateField(default=date.today)
    
    def __str__(self):
        return f"{self.nombre} (Vigente desde {self.vigente_desde})"
    
    class Meta:
        verbose_name_plural = "Parámetros Legales (Verificar)"


class LiquidacionSueldo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='liquidaciones')
    mes = models.IntegerField(validators=[MinValueValidator(1)])
    anio = models.IntegerField(validators=[MinValueValidator(2000)])
    
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=0)
    gratificacion_legal = models.DecimalField(max_digits=12, decimal_places=0)
    horas_extra_monto = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    # Snapshot of parameters at the time of creation
    valor_uf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    @property
    def total_imponible(self):
        suma_haberes_imp = sum(h.monto for h in self.haberes.filter(imponible=True))
        return self.sueldo_base + self.gratificacion_legal + self.horas_extra_monto + suma_haberes_imp
        
    @property
    def total_no_imponible(self):
        return sum(h.monto for h in self.haberes.filter(imponible=False))
        
    @property
    def total_haberes(self):
        return self.total_imponible + self.total_no_imponible
        
    @property
    def descuento_afp(self):
        tope = self.get_tope_imponible()
        base = min(self.total_imponible, tope) if tope > 0 else self.total_imponible
        return (base * (Decimal('10') + self.empleado.afp.comision_porcentaje)) / 100
        
    @property
    def descuento_salud(self):
        tope = self.get_tope_imponible()
        base = min(self.total_imponible, tope) if tope > 0 else self.total_imponible
        if self.empleado.sistema_salud == 'Fonasa':
            # Buscar parámetro Fonasa o default a 7%
            return (base * Decimal('7.0')) / 100
        else: # Isapre
            if self.empleado.isapre_plan_uf and self.valor_uf:
                # El 7% mínimo vs plan pactado
                siete_pct = (base * Decimal('7.0')) / 100
                monto_plan = self.empleado.isapre_plan_uf * self.valor_uf
                return max(siete_pct, monto_plan)
            return (base * Decimal('7.0')) / 100

    @property
    def descuento_cesantia(self):
        if self.empleado.tipo_contrato == 'Plazo Fijo' or self.empleado.tipo_contrato == 'Por Obra/Faena':
            return Decimal('0')
        tope = self.get_tope_imponible_seguro_cesantia()
        base = min(self.total_imponible, tope) if tope > 0 else self.total_imponible
        return (base * Decimal('0.6')) / 100
        
    def get_tope_imponible(self):
        try:
            param = ParametroLegal.objects.filter(nombre="Tope Imponible AFP (UF)").order_by('-vigente_desde').first()
            if param and param.valor_moneda and self.valor_uf:
                return param.valor_moneda * self.valor_uf
        except: pass
        return 0
        
    def get_tope_imponible_seguro_cesantia(self):
        try:
            param = ParametroLegal.objects.filter(nombre="Tope Imponible AFC (UF)").order_by('-vigente_desde').first()
            if param and param.valor_moneda and self.valor_uf:
                return param.valor_moneda * self.valor_uf
        except: pass
        return 0

    @property
    def total_tributable(self):
        res = self.total_imponible - (self.descuento_afp + self.descuento_salud + self.descuento_cesantia)
        return max(Decimal('0'), res)

    @property
    def impuesto_unico(self):
        # Fetch matching month params
        from datetime import date
        dt = date(self.anio, self.mes, 1)
        tramos = TablaImpuestoUnico.objects.filter(mes_vigencia=dt)
        if not tramos.exists():
            return Decimal('0')
            
        tributable = self.total_tributable
        utm = tramos.first().valor_utm
        tributable_utm = tributable / utm if utm > 0 else 0
        
        for tramo in tramos:
            desde = tramo.tramo_desde_utm
            hasta = tramo.tramo_hasta_utm
            if hasta is None or (desde <= tributable_utm <= hasta) or (desde <= tributable_utm and hasta is None):
                impuesto = (tributable * tramo.factor) - tramo.rebaja
                return max(Decimal('0'), impuesto)
        return Decimal('0')
        
    @property
    def total_descuentos(self):
        desc_add = sum(d.monto for d in self.descuentos.all())
        return self.descuento_afp + self.descuento_salud + self.descuento_cesantia + self.impuesto_unico + desc_add
        
    @property
    def liquido_a_pago(self):
        return max(Decimal('0'), self.total_haberes - self.total_descuentos)

    class Meta:
        unique_together = ('empleado', 'mes', 'anio')
        ordering = ['-anio', '-mes', 'empleado__nombre_completo']


class HaberAdicional(models.Model):
    liquidacion = models.ForeignKey(LiquidacionSueldo, on_delete=models.CASCADE, related_name='haberes')
    nombre = models.CharField(max_length=150)
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    imponible = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre}: ${self.monto}"


class DescuentoAdicional(models.Model):
    liquidacion = models.ForeignKey(LiquidacionSueldo, on_delete=models.CASCADE, related_name='descuentos')
    nombre = models.CharField(max_length=150)
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    
    def __str__(self):
        return f"{self.nombre}: ${self.monto}"
