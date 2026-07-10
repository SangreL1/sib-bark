import calendar
from datetime import date
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

from django.forms import modelformset_factory
from .models import Empleado, LiquidacionSueldo, Asistencia, AFP, ParametroLegal, TablaImpuestoUnico
from .forms import AFPForm, ParametroLegalForm, TablaImpuestoUnicoForm, EmpleadoForm

@login_required
def empleado_list(request):
    empleados = Empleado.objects.all().order_by('nombre_completo')
    return render(request, 'rrhh/empleado_list.html', {'empleados': empleados})


@login_required
def empleado_create(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            try:
                emp = form.save()
                messages.success(request, f'Empleado {emp.nombre_completo} creado exitosamente.')
                return redirect('empleado_list')
            except Exception as e:
                messages.error(request, f'Error al guardar en base de datos: {e}')
        else:
            messages.error(request, 'Ocurrió un error. Revisa los datos y el formato del RUT.')
    else:
        form = EmpleadoForm()
    
    return render(request, 'rrhh/empleado_form.html', {'form': form, 'titulo': 'Nuevo Empleado'})


@login_required
def empleado_detail(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    liquidaciones = LiquidacionSueldo.objects.filter(empleado=empleado).order_by('-anio', '-mes')
    
    # Resumen mes actual
    hoy = date.today()
    asistencias = Asistencia.objects.filter(
        empleado=empleado,
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).order_by('-fecha')
    
    return render(request, 'rrhh/empleado_detail.html', {
        'empleado': empleado,
        'liquidaciones': liquidaciones,
        'asistencias': asistencias,
        'hoy': hoy
    })


@login_required
def liquidacion_generar(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    if request.method == 'POST':
        mes = int(request.POST.get('mes'))
        anio = int(request.POST.get('anio'))
        
        if LiquidacionSueldo.objects.filter(empleado=empleado, mes=mes, anio=anio).exists():
            messages.warning(request, f'Ya existe una liquidación generada para el periodo {mes}/{anio}.')
            return redirect('empleado_detail', empleado_id=empleado.id)
            
        # Gratificación
        tope_grat = Decimal('4.75') * Decimal('500000') / Decimal('12') # IMM ref 500k
        grat_calculada = empleado.sueldo_base * Decimal('0.25')
        grat = min(grat_calculada, tope_grat)
        
        # Horas extra
        asistencias = Asistencia.objects.filter(empleado=empleado, fecha__year=anio, fecha__month=mes)
        horas_ex = sum(a.horas_extra for a in asistencias)
        factor_hora_extra = Decimal('0.0077777') # (1/30) * 28 / 180 * 1.5 para 44 hrs
        monto_hex = empleado.sueldo_base * factor_hora_extra * horas_ex
        
        liq = LiquidacionSueldo.objects.create(
            empleado=empleado,
            mes=mes,
            anio=anio,
            sueldo_base=empleado.sueldo_base,
            gratificacion_legal=grat,
            horas_extra_monto=monto_hex,
            valor_uf=Decimal('38000') # Valor por defecto rápido
        )
        messages.success(request, f'Liquidación de {mes}/{anio} generada base. Puede añadir haberes/descuentos desde panel si requiere.')
        
    return redirect('empleado_detail', empleado_id=empleado.id)


@login_required
def asistencia_mensual(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    mes = int(request.GET.get('mes', date.today().month))
    anio = int(request.GET.get('anio', date.today().year))
    
    # Create or get days in the month
    num_days = calendar.monthrange(anio, mes)[1]
    
    for day in range(1, num_days + 1):
        dt = date(anio, mes, day)
        Asistencia.objects.get_or_create(empleado=empleado, fecha=dt)
        
    if request.method == 'POST':
        for day in range(1, num_days + 1):
            dt = date(anio, mes, day)
            asistencia = Asistencia.objects.get(empleado=empleado, fecha=dt)
            tipo_val = request.POST.get(f'tipo_{day}')
            horas_trabajadas = request.POST.get(f'horas_trabajadas_{day}')
            horas_extra = request.POST.get(f'horas_extra_{day}')
            
            if tipo_val: asistencia.tipo = tipo_val
            if horas_trabajadas: asistencia.horas_trabajadas = Decimal(horas_trabajadas)
            if horas_extra: asistencia.horas_extra = Decimal(horas_extra)
            asistencia.save()
            
        messages.success(request, f'Asistencia del mes {mes}/{anio} guardada exitosamente.')
        return redirect('asistencia_mensual', empleado_id=empleado.id)
        
    asistencias = Asistencia.objects.filter(
        empleado=empleado, fecha__year=anio, fecha__month=mes
    ).order_by('fecha')
    
    presentes = asistencias.filter(tipo='Presente').count()
    faltas = asistencias.filter(tipo__in=['Falta Justificada', 'Falta Injustificada']).count()
    total_extras = sum(a.horas_extra for a in asistencias)
    
    context = {
        'empleado': empleado,
        'mes': mes,
        'anio': anio,
        'asistencias': asistencias,
        'presentes': presentes,
        'faltas': faltas,
        'total_extras': total_extras,
    }
    return render(request, 'rrhh/asistencia_mensual.html', context)


@login_required
def liquidacion_pdf(request, empleado_id, mes, anio):
    liquidacion = get_object_or_404(LiquidacionSueldo, empleado_id=empleado_id, mes=mes, anio=anio)
    empleado = liquidacion.empleado
    
    # Calculate worked days (based on 30 - ausencias)
    asistencias = Asistencia.objects.filter(empleado=empleado, fecha__year=anio, fecha__month=mes)
    faltas = asistencias.filter(tipo__in=['Falta Justificada', 'Falta Injustificada', 'Licencia Médica']).count()
    dias_trabajados = 30 - faltas
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Liquidacion_{empleado.rut}_{mes}_{anio}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    style_title = ParagraphStyle(name='TitleRight', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', alignment=2)
    style_normal = ParagraphStyle(name='NormalSmall', parent=styles['Normal'], fontSize=8, fontName='Helvetica', leading=10)
    style_bold = ParagraphStyle(name='BoldSmall', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', leading=10)

    def num(valor):
        return f"${valor:,.0f}".replace(",", ".")
        
    # --- HEADER EMPRESA ---
    header_data = [
        [
            Paragraph("<b>CONSTRUCTORA SIB BARK SPA</b><br/>RUT: 76.123.456-7<br/>Giro: Construcción<br/>Dirección: Antofagasta, Chile", style_normal),
            Paragraph(f"<b>LIQUIDACIÓN DE REMUNERACIONES</b><br/>Periodo: <b>{mes:02d}/{anio}</b>", style_title)
        ]
    ]
    t_header = Table(header_data, colWidths=[300, 230])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_header)
    
    # --- DATOS TRABAJADOR ---
    trabajador_data = [
        ["RUT:", empleado.rut, "FECHA INGRESO:", empleado.fecha_ingreso.strftime("%d-%m-%Y") if empleado.fecha_ingreso else "--"],
        ["NOMBRE:", empleado.nombre_completo, "CARGO:", empleado.cargo],
        ["SUELDO BASE:", num(liquidacion.sueldo_base), "DÍAS TRABAJADOS:", f"{dias_trabajados} días"],
        ["SIST. PREVISIONAL:", f"AFP {empleado.afp.nombre} ({(10 + empleado.afp.comision_porcentaje):.2f}%)", "SIST. SALUD:", empleado.sistema_salud],
        ["PLAN DE SALUD:", f"{empleado.isapre_plan_uf} UF" if (empleado.sistema_salud=='Isapre' and empleado.isapre_plan_uf) else "7% Legal", "CENTRO COSTO:", empleado.unidad_negocio],
        ["TIPO CONTRATO:", empleado.tipo_contrato, "", ""],
    ]
    
    t_trab = Table(trabajador_data, colWidths=[100, 165, 100, 165])
    t_trab.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('BOX', (0,0), (-1,-1), 1, colors.Color(0,0,0,0.5)),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.Color(0,0,0,0.1)),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_trab)
    story.append(Spacer(1, 15))
    
    # --- HABERES Y DESCUENTOS ---
    imponibles_data = []
    imponibles_data.append(["Sueldo Base Mensual", num(liquidacion.sueldo_base)])
    imponibles_data.append(["Gratificación Legal", num(liquidacion.gratificacion_legal)])
    
    if liquidacion.horas_extra_monto > 0:
        imponibles_data.append([f"Horas Extra", num(liquidacion.horas_extra_monto)])
        
    for hi in liquidacion.haberes.filter(imponible=True):
        imponibles_data.append([hi.nombre, num(hi.monto)])
        
    no_imponibles_data = []
    for hni in liquidacion.haberes.filter(imponible=False):
        no_imponibles_data.append([hni.nombre, num(hni.monto)])
        
    descuentos_data = []
    
    # Desglose de AFP para mayor transparencia
    tope = liquidacion.get_tope_imponible()
    base_calc = min(liquidacion.total_imponible, tope) if tope > 0 else liquidacion.total_imponible
    afp_10 = (base_calc * Decimal('10.0')) / 100
    afp_com = liquidacion.descuento_afp - afp_10
    descuentos_data.append([f"Fondo Pensiones (10%)", num(afp_10)])
    if afp_com > 0:
        descuentos_data.append([f"Comisión AFP ({empleado.afp.comision_porcentaje}%)", num(afp_com)])
        
    # Desglose de Salud
    if empleado.sistema_salud == 'Fonasa':
        descuentos_data.append([f"Cotización Salud (7%)", num(liquidacion.descuento_salud)])
    else:
        salud_7 = (base_calc * Decimal('7.0')) / 100
        descuentos_data.append([f"Salud Obligatoria (7%)", num(salud_7)])
        adicional = liquidacion.descuento_salud - salud_7
        if adicional > 0:
            descuentos_data.append([f"Adicional Isapre", num(adicional)])

    descuentos_data.append([f"Seguro Cesantía (AFC)", num(liquidacion.descuento_cesantia)])
    descuentos_data.append([f"Impuesto Único 2da Cat.", num(liquidacion.impuesto_unico)])
    
    for d in liquidacion.descuentos.all():
        descuentos_data.append([d.nombre, num(d.monto)])
        
    # Matching table lengths to create 2 robust columns
    haberes_totales_list = imponibles_data + [["--- Haberes No Imponibles ---", ""]] + no_imponibles_data
    
    max_len = max(len(haberes_totales_list), len(descuentos_data))
    while len(haberes_totales_list) < max_len: haberes_totales_list.append(["", ""])
    while len(descuentos_data) < max_len: descuentos_data.append(["", ""])
    
    combined_data = [[
        Paragraph("<b>DESCRIPCIÓN HABERES</b>", style_bold), Paragraph("<b>MONTO</b>", style_bold), 
        Paragraph("<b>DESCRIPCIÓN DESCUENTOS</b>", style_bold), Paragraph("<b>MONTO</b>", style_bold)
    ]]
    for i in range(max_len):
        combined_data.append([
            haberes_totales_list[i][0], haberes_totales_list[i][1],
            descuentos_data[i][0], descuentos_data[i][1]
        ])
        
    # Agregamos filas vacías para empujar los totales abajo si hay pocos items
    for _ in range(3):
        combined_data.append(["", "", "", ""])
        
    combined_data.append([
        "TOTAL HABERES:", num(liquidacion.total_haberes),
        "TOTAL DESCUENTOS:", num(liquidacion.total_descuentos)
    ])
        
    t_detalle = Table(combined_data, colWidths=[185, 80, 185, 80])
    
    table_styles = [
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9, 0.9, 0.9)),
        ('ALIGN', (1,1), (1,-1), 'RIGHT'),
        ('ALIGN', (3,1), (3,-1), 'RIGHT'),
        ('BOX', (0,0), (-1,-1), 1, colors.Color(0,0,0,0.5)),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.Color(0,0,0,0.5)),
        ('LINEBEFORE', (2,0), (2,-1), 1, colors.Color(0,0,0,0.5)),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Ultima fila bold
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.Color(0,0,0,0.5)), # Linea sobre el total
    ]
    t_detalle.setStyle(TableStyle(table_styles))
    story.append(t_detalle)
    story.append(Spacer(1, 15))
    
    # --- RESUMEN Y TOTALES ---
    resumen_data = [
        ["Total Imponible:", num(liquidacion.total_imponible), "ALCANCE LÍQUIDO:", num(liquidacion.liquido_a_pago)],
        ["Total Tributable:", num(liquidacion.total_tributable), "ANTICIPOS:", "$0"],
        ["Base Tributable (UTM):", f"{(liquidacion.total_tributable / (liquidacion.valor_uf or 1)):.2f}" if liquidacion.valor_uf else "0.00", "LÍQUIDO A PAGO:", num(liquidacion.liquido_a_pago)],
    ]
    
    t_resumen = Table(resumen_data, colWidths=[120, 145, 130, 135])
    t_resumen.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTNAME', (3,-1), (3,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (3,-1), (3,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
        ('BOX', (0,0), (-1,-1), 1, colors.Color(0,0,0,0.5)),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.Color(0,0,0,0.1)),
        ('BACKGROUND', (2,2), (3,2), colors.Color(0.2, 0.6, 0.86, alpha=0.15)), # Highlighter liquido
    ]))
    story.append(t_resumen)
    story.append(Spacer(1, 20))
    
    # En Letras
    num_str = f"{liquidacion.liquido_a_pago:,.0f} PESOS".replace(",", ".")
    story.append(Paragraph(f"<b>SON:</b> {num_str}", style_normal))
    story.append(Spacer(1, 40))
    
    # --- FIRMAS ---
    nota_legal = "Certifico que he recibido de mi empleador el pago total de las remuneraciones detalladas en esta liquidación, las que cubren exactamente todos los montos correspondientes a los servicios prestados durante este período, no existiendo saldo a mi favor."
    story.append(Paragraph(nota_legal, ParagraphStyle('Legal', parent=styles['Normal'], fontSize=7, alignment=4, textColor=colors.Color(0.3,0.3,0.3))))
    story.append(Spacer(1, 60))
    
    firma_data = [
        ["____________________________________", "____________________________________"],
        ["FIRMA DEL TRABAJADOR", "FIRMA DEL EMPLEADOR"]
    ]
    t_firma = Table(firma_data, colWidths=[265, 265])
    t_firma.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,1), (-1,1), 8),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
    ]))
    story.append(t_firma)
    
    doc.build(story)
    return response

@login_required
def configuracion_legal(request):
    AFPFormSet = modelformset_factory(AFP, form=AFPForm, extra=0)
    ParamLegalFormSet = modelformset_factory(ParametroLegal, form=ParametroLegalForm, extra=0)
    TablaImpuestoFormSet = modelformset_factory(TablaImpuestoUnico, form=TablaImpuestoUnicoForm, extra=0)
    
    if request.method == 'POST':
        afp_formset = AFPFormSet(request.POST, prefix='afp')
        param_formset = ParamLegalFormSet(request.POST, prefix='param')
        tabla_formset = TablaImpuestoFormSet(request.POST, prefix='tabla')
        
        # Guardar valor global UTM en Tabla Impuesto
        utm_global = request.POST.get('utm_global')
        
        if afp_formset.is_valid() and param_formset.is_valid() and tabla_formset.is_valid():
            afp_formset.save()
            param_formset.save()
            
            # Save tabla with UTM manual update
            tramos = tabla_formset.save(commit=False)
            for tramo in tramos:
                if utm_global:
                    tramo.valor_utm = Decimal(utm_global)
                tramo.save()
                
            messages.success(request, 'Configuración legal actualizada exitosamente.')
            return redirect('configuracion_legal')
        else:
            messages.error(request, 'Hubo errores en los formularios. Revisa los datos ingresados.')
    else:
        afp_formset = AFPFormSet(queryset=AFP.objects.all(), prefix='afp')
        param_formset = ParamLegalFormSet(queryset=ParametroLegal.objects.all(), prefix='param')
        tabla_formset = TablaImpuestoFormSet(queryset=TablaImpuestoUnico.objects.all(), prefix='tabla')
    
    # Extraer el valor actual de UTM para mostrarlo arriba
    actual_utm = TablaImpuestoUnico.objects.first().valor_utm if TablaImpuestoUnico.objects.exists() else 0
    
    context = {
        'afp_formset': afp_formset,
        'param_formset': param_formset,
        'tabla_formset': tabla_formset,
        'actual_utm': actual_utm,
    }
    return render(request, 'rrhh/configuracion_legal.html', context)


@login_required
def rrhh_dashboard(request):
    total_empleados = Empleado.objects.filter(activo=True).count()
    total_sueldos = sum(e.sueldo_base for e in Empleado.objects.filter(activo=True))
    
    hoy = date.today()
    liq_mes_actual = LiquidacionSueldo.objects.filter(mes=hoy.month, anio=hoy.year).count()
    
    context = {
        'total_empleados': total_empleados,
        'total_sueldos': total_sueldos,
        'liq_mes_actual': liq_mes_actual,
        'hoy': hoy
    }
    return render(request, 'rrhh/dashboard.html', context)


@login_required
def empleado_delete(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    if request.method == 'POST':
        nombre = empleado.nombre_completo
        empleado.delete()
        messages.success(request, f'Empleado {nombre} eliminado correctamente.')
        return redirect('empleado_list')
    return render(request, 'rrhh/empleado_confirm_delete.html', {'empleado': empleado})


@login_required
def asistencia_masiva(request):
    fecha_str = request.GET.get('fecha', str(date.today()))
    try:
        fecha_obj = date.fromisoformat(fecha_str)
    except ValueError:
        fecha_obj = date.today()
        fecha_str = str(fecha_obj)
        
    empleados = Empleado.objects.filter(activo=True).order_by('nombre_completo')
    
    if request.method == 'POST':
        fecha_post = request.POST.get('fecha_post')
        for emp in empleados:
            tipo = request.POST.get(f'tipo_{emp.id}')
            horas_trabajadas = request.POST.get(f'horas_trabajadas_{emp.id}')
            horas_extra = request.POST.get(f'horas_extra_{emp.id}')
            if tipo:
                asistencia, created = Asistencia.objects.get_or_create(
                    empleado=emp, fecha=fecha_post,
                    defaults={'tipo': 'Presente', 'horas_trabajadas': Decimal('8.0')}
                )
                asistencia.tipo = tipo
                if horas_trabajadas: asistencia.horas_trabajadas = Decimal(horas_trabajadas)
                if horas_extra: asistencia.horas_extra = Decimal(horas_extra)
                asistencia.save()
        messages.success(request, f'Asistencia masiva guardada para la fecha {fecha_post}.')
        return redirect(f'/rrhh/asistencia/masiva/?fecha={fecha_post}')
    
    # Preparar datos para el form
    asistencia_data = []
    for emp in empleados:
        asis = Asistencia.objects.filter(empleado=emp, fecha=fecha_obj).first()
        asistencia_data.append({
            'empleado': emp,
            'asistencia': asis
        })
        
    return render(request, 'rrhh/asistencia_masiva.html', {
        'fecha_obj': fecha_obj,
        'fecha_str': fecha_str,
        'asistencia_data': asistencia_data,
        'tipos_choices': Asistencia.TIPO_ASISTENCIA_CHOICES
    })


@login_required
def asistencia_mensual_llena(request, empleado_id):
    """Marca todos los días del mes como presente"""
    if request.method == 'POST':
        empleado = get_object_or_404(Empleado, id=empleado_id)
        mes = int(request.POST.get('mes'))
        anio = int(request.POST.get('anio'))
        num_days = calendar.monthrange(anio, mes)[1]
        for day in range(1, num_days + 1):
            dt = date(anio, mes, day)
            asistencia, created = Asistencia.objects.get_or_create(empleado=empleado, fecha=dt)
            asistencia.tipo = 'Presente'
            if created or not asistencia.horas_trabajadas:
                asistencia.horas_trabajadas = Decimal('8.0')
            asistencia.save()
        messages.success(request, f'Todos los días del mes {mes}/{anio} marcados como Presente.')
        return redirect(f'/rrhh/empleado/{empleado_id}/asistencia/?mes={mes}&anio={anio}')
    return redirect('empleado_list')
