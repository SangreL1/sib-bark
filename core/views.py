import os
import pandas as pd
from decimal import Decimal
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone

from .models import OrdenCompra, FMR, Entrega, Costo, Trazabilidad, ItemOC, PackingListItem, Factura, CostoMaterial, CostoManoObra
from .forms import OrdenCompraForm, OrdenCompraEditForm, FMRForm, EntregaForm, CostoForm, ItemOCForm, PackingListItemForm, FacturaForm, CostoMaterialForm, CostoManoObraForm


# ──────────────────────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('project_list')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'project_list'))
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD (KPI overview — accessed from navbar)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    from datetime import date
    from dateutil.relativedelta import relativedelta

    # ── Totales globales ─────────────────────────────────────────────────────
    total_ocs       = OrdenCompra.objects.count()
    total_revenue   = OrdenCompra.objects.aggregate(t=Sum('valor_total'))['t'] or Decimal('0.00')
    
    # Sumar costos generales, materiales de compras detalladas y mano de obra
    total_costs_general = Costo.objects.aggregate(t=Sum('monto'))['t'] or Decimal('0.00')
    total_materials = sum(mc.total for mc in CostoMaterial.objects.all())
    total_mano_obra = sum(moc.total for moc in CostoManoObra.objects.all())
    
    total_costs     = total_costs_general + total_materials + total_mano_obra
    global_margin   = total_revenue - total_costs
    global_margin_pct = float(global_margin / total_revenue * 100) if total_revenue > 0 else 0

    # ── OC por estado ────────────────────────────────────────────────────────
    status_counts = (
        OrdenCompra.objects.values('estado')
        .annotate(count=Count('numero_oc'))
        .order_by('estado')
    )
    status_dict = {item['estado']: item['count'] for item in status_counts}

    # ── Semaforos: conteo por color ──────────────────────────────────────────
    # No se pueden hacer con annotate puro (son @property), pero se calculan
    # en Python sobre el queryset ya cargado — es un conjunto pequeño.
    todas_ocs = OrdenCompra.objects.only(
        'numero_oc', 'estado', 'fecha_compromiso', 'porcentaje_entregado'
    )
    semaforos = {'plazo': {'green':0,'yellow':0,'red':0,'grey':0},
                 'avance': {'green':0,'yellow':0,'red':0,'grey':0},
                 'docs': {'green':0,'yellow':0,'red':0,'grey':0}}
    for oc in todas_ocs:
        semaforos['plazo'][oc.semaforo_plazo]   += 1
        semaforos['avance'][oc.semaforo_avance] += 1
    # docs requiere prefetch de fmrs; lo calculamos sobre las primeras 200
    ocs_docs = OrdenCompra.objects.prefetch_related('fmrs').only(
        'numero_oc','oc_link','oc_file','plano_link','plano_file','fmr_link','fmr_file'
    )[:200]
    for oc in ocs_docs:
        semaforos['docs'][oc.semaforo_docs] += 1

    # ── Monto pendiente de facturar ──────────────────────────────────────────
    # OC sin facturas o con todas sus facturas en estado 'pendiente'
    ocs_sin_factura = OrdenCompra.objects.filter(
        facturas__isnull=True
    ).aggregate(t=Sum('valor_total'))['t'] or Decimal('0.00')
    facturas_pendientes_monto = (
        Factura.objects.filter(estado='pendiente')
        .aggregate(t=Sum('monto'))['t'] or Decimal('0.00')
    )
    monto_pendiente_facturar = ocs_sin_factura + facturas_pendientes_monto

    # ── Top clientes por monto total ─────────────────────────────────────────
    top_clientes_monto = (
        OrdenCompra.objects
        .values('cliente')
        .annotate(total_monto=Sum('valor_total'), total_ocs=Count('numero_oc'))
        .order_by('-total_monto')[:8]
    )

    # ── Top clientes por margen (calculado en Python, top 8 ya cargados) ─────
    # Unimos costos por cliente para calcular el margen preciso
    clientes_margen = []
    for row in top_clientes_monto:
        cliente_name = row['cliente']
        costos_general = (
            Costo.objects
            .filter(orden_compra__cliente=cliente_name)
            .aggregate(t=Sum('monto'))['t'] or Decimal('0.00')
        )
        costos_mat = sum(
            mc.total for mc in CostoMaterial.objects.filter(orden_compra__cliente=cliente_name)
        )
        costos_mo = sum(
            moc.total for moc in CostoManoObra.objects.filter(orden_compra__cliente=cliente_name)
        )
        
        costos_cliente = costos_general + costos_mat + costos_mo
        monto = row['total_monto'] or Decimal('0.00')
        margen = monto - costos_cliente
        margen_pct = float(margen / monto * 100) if monto > 0 else 0
        clientes_margen.append({
            'cliente': cliente_name,
            'total_monto': monto,
            'total_ocs': row['total_ocs'],
            'margen': margen,
            'margen_pct': round(margen_pct, 1),
        })
    clientes_margen.sort(key=lambda x: x['margen'], reverse=True)

    # ── Reporte mensual ultimos 6 meses ──────────────────────────────────────
    hoy = date.today()
    meses = []
    for i in range(5, -1, -1):
        inicio = (hoy - relativedelta(months=i)).replace(day=1)
        fin    = (inicio + relativedelta(months=1))
        ocs_mes = OrdenCompra.objects.filter(
            fecha_oc__gte=inicio, fecha_oc__lt=fin
        ).aggregate(
            cantidad=Count('numero_oc'),
            monto=Sum('valor_total')
        )
        facturas_mes = Factura.objects.filter(
            fecha_emision__gte=inicio, fecha_emision__lt=fin
        ).aggregate(facturado=Sum('monto'))
        meses.append({
            'mes': inicio.strftime('%b %Y'),
            'cantidad_ocs': ocs_mes['cantidad'] or 0,
            'monto_ocs': ocs_mes['monto'] or Decimal('0.00'),
            'facturado': facturas_mes['facturado'] or Decimal('0.00'),
        })

    # ── Listas de detalle ────────────────────────────────────────────────────
    recent_deliveries = Entrega.objects.select_related('orden_compra').order_by('-fecha_entrega')[:6]
    pending_ocs       = OrdenCompra.objects.filter(
        estado__in=['En proceso','Pendiente']
    ).order_by('fecha_compromiso')[:6]
    cost_by_category  = Costo.objects.values('categoria').annotate(total=Sum('monto')).order_by('-total')

    context = {
        'total_ocs': total_ocs,
        'total_revenue': total_revenue,
        'total_costs': total_costs,
        'global_margin': global_margin,
        'global_margin_pct': round(global_margin_pct, 2),
        'status_dict': status_dict,
        'semaforos': semaforos,
        'monto_pendiente_facturar': monto_pendiente_facturar,
        'clientes_margen': clientes_margen,
        'reporte_meses': meses,
        'recent_deliveries': recent_deliveries,
        'pending_ocs': pending_ocs,
        'cost_by_category': cost_by_category,
    }
    return render(request, 'core/dashboard.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# PROJECT LIST — Main screen
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def project_list(request):
    queryset = OrdenCompra.objects.all().prefetch_related('fmrs', 'entregas')

    # Filters
    q = request.GET.get('q', '').strip()
    estado_filter = request.GET.get('estado', '')

    if q:
        queryset = queryset.filter(
            Q(numero_oc__icontains=q) |
            Q(cliente__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(proyecto__icontains=q) |
            Q(guia_despacho_resumen__icontains=q) |
            Q(factura_resumen__icontains=q) |
            Q(fmrs__fmr_code__icontains=q) |
            Q(facturas__numero_factura__icontains=q)  # busqueda en modelo Factura
        ).distinct()

    if estado_filter:
        queryset = queryset.filter(estado=estado_filter)

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    estados = OrdenCompra.ESTADOS

    context = {
        'page_obj': page_obj,
        'q': q,
        'estado_filter': estado_filter,
        'estados': estados,
        'total_count': queryset.count(),
    }
    return render(request, 'core/project_list.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# SEARCH
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    results_oc = []
    results_fmr = []

    if query:
        results_oc = OrdenCompra.objects.filter(
            Q(numero_oc__icontains=query) |
            Q(cliente__icontains=query) |
            Q(proyecto__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(guia_despacho_resumen__icontains=query) |
            Q(factura_resumen__icontains=query)
        ).distinct()

        results_fmr = FMR.objects.filter(
            Q(fmr_code__icontains=query) |
            Q(guia_despacho__icontains=query) |
            Q(factura__icontains=query) |
            Q(cotizacion__icontains=query)
        ).distinct()

        if len(results_oc) == 1 and len(results_fmr) == 0:
            return redirect('project_detail', numero_oc=results_oc[0].numero_oc)
        elif len(results_fmr) == 1 and len(results_oc) == 0:
            if results_fmr[0].orden_compra:
                return redirect('project_detail', numero_oc=results_fmr[0].orden_compra.numero_oc)
        elif len(results_oc) == 1 and len(results_fmr) == 1:
            if results_fmr[0].orden_compra == results_oc[0]:
                return redirect('project_detail', numero_oc=results_oc[0].numero_oc)

    context = {'query': query, 'results_oc': results_oc, 'results_fmr': results_fmr}
    return render(request, 'core/search_results.html', context)


def registrar_trazabilidad(orden_compra, accion, detalle, usuario):
    Trazabilidad.objects.create(
        orden_compra=orden_compra,
        usuario=usuario if usuario and usuario.is_authenticated else None,
        accion=accion,
        detalle=detalle
    )

# ──────────────────────────────────────────────────────────────────────────────
# OC CRUD
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def oc_create(request):
    if request.method == 'POST':
        form = OrdenCompraForm(request.POST, request.FILES)
        if form.is_valid():
            oc = form.save()
            registrar_trazabilidad(
                oc, 
                "Creación de OC", 
                f"Orden de Compra {oc.numero_oc} registrada en el sistema.", 
                request.user
            )
            messages.success(request, f'Orden de Compra {oc.numero_oc} creada exitosamente.')
            return redirect('project_detail', numero_oc=oc.numero_oc)
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = OrdenCompraForm()

    return render(request, 'core/oc_form.html', {'form': form, 'titulo': 'Nueva Orden de Compra', 'is_create': True})


@login_required
def oc_edit(request, numero_oc):
    project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
    if request.method == 'POST':
        form = OrdenCompraEditForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            registrar_trazabilidad(
                project, 
                "Modificación de OC", 
                "Se actualizaron los datos o el respaldo documental de la Orden de Compra.", 
                request.user
            )
            messages.success(request, 'Proyecto actualizado correctamente.')
            return redirect('project_detail', numero_oc=numero_oc)
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = OrdenCompraEditForm(instance=project)

    return render(request, 'core/oc_form.html', {
        'form': form, 'project': project,
        'titulo': f'Editar OC: {numero_oc}', 'is_create': False
    })


# ──────────────────────────────────────────────────────────────────────────────
# PROJECT DETAIL
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def project_detail(request, numero_oc):
    project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)

    # ── CARGAR COSTOS TRADICIONALES Y DETALLADOS ─────────────────────────────
    costs = project.costos.all().order_by('-fecha')
    costs_general_total = costs.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    # Costos detallados de materiales
    material_costs = project.costos_materiales.all()
    material_total = sum(mc.total for mc in material_costs)

    # Costos detallados de mano de obra
    mano_obra_costs = project.costos_mano_obra.all()
    mano_obra_total = sum(moc.total for moc in mano_obra_costs)

    # Gran total costos (general + materiales + mano de obra)
    costs_total = costs_general_total + material_total + mano_obra_total

    budget = project.valor_total or Decimal('0.00')
    margin = budget - costs_total
    margin_pct = float(margin / budget * 100) if budget > 0 else 0
    budget_used_pct = float(costs_total / budget * 100) if budget > 0 else 0

    fmrs = project.fmrs.all()
    deliveries = project.entregas.prefetch_related('packing_list_items__item_oc').all().order_by('-fecha_entrega')
    items = project.items.all().order_by('linea')
    trazabilidades = project.trazabilidades.all().order_by('-fecha_hora')

    # ── CALCULOS POR KILO (BOM) ──────────────────────────────────────────────
    total_weight = sum(item.peso_total_kg for item in items)
    items_total_value = sum(item.valor_total for item in items)

    # Cálculos detallados por kilo
    costo_por_kilo = costs_total / total_weight if total_weight > 0 else Decimal('0.00')
    utilidad_por_kilo = margin / total_weight if total_weight > 0 else Decimal('0.00')

    # Formularios
    entrega_form = EntregaForm()
    fmr_form = FMRForm()
    costo_form = CostoForm(initial={'fecha': timezone.now().date()})
    item_form = ItemOCForm()
    packing_list_form = PackingListItemForm(orden_compra=project)
    
    # Nuevos formularios detallados
    costo_material_form = CostoMaterialForm(initial={'fecha_compra': timezone.now().date()})
    costo_mano_obra_form = CostoManoObraForm()

    context = {
        'project': project,
        'costs': costs,
        'material_costs': material_costs,
        'mano_obra_costs': mano_obra_costs,
        
        # Totales agregados
        'costs_general_total': costs_general_total,
        'material_total': material_total,
        'mano_obra_total': mano_obra_total,
        'costs_total': costs_total,
        'margin': margin,
        'margin_pct': round(margin_pct, 2),
        'budget_used_pct': min(round(budget_used_pct, 2), 100),
        
        'fmrs': fmrs,
        'deliveries': deliveries,
        'items': items,
        'trazabilidades': trazabilidades,
        'total_weight': total_weight,
        'items_total_value': items_total_value,
        
        # Indicadores por Kilo
        'costo_por_kilo': round(costo_por_kilo, 2),
        'utilidad_por_kilo': round(utilidad_por_kilo, 2),
        
        # Formularios
        'entrega_form': entrega_form,
        'fmr_form': fmr_form,
        'costo_form': costo_form,
        'item_form': item_form,
        'packing_list_form': packing_list_form,
        'costo_material_form': costo_material_form,
        'costo_mano_obra_form': costo_mano_obra_form,
        'dias_restantes': project.dias_restantes_calculado,
    }
    return render(request, 'core/project_detail.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# INLINE ACTIONS (POST only — redirect back to detail)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def add_cost(request, numero_oc):
    if request.method == 'POST':
        project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
        form = CostoForm(request.POST)
        if form.is_valid():
            costo = form.save(commit=False)
            costo.orden_compra = project
            costo.save()
            registrar_trazabilidad(
                project,
                "Registro de Costo",
                f"Se registró un gasto en categoría '{costo.categoria}' por ${costo.monto:,.0f}. Detalle: {costo.descripcion} (Ref: {costo.documento_referencia or 'Sin ref'})",
                request.user
            )
            messages.success(request, f'Gasto de ${costo.monto:,.0f} registrado en Centro de Costos.')
        else:
            messages.error(request, f'Error al registrar gasto: {form.errors}')
    return redirect('project_detail', numero_oc=numero_oc)


@login_required
def add_entrega(request, numero_oc):
    if request.method == 'POST':
        project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
        form = EntregaForm(request.POST, request.FILES)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.orden_compra = project
            entrega.save()
            # Recalculate % delivered
            project.recalcular_porcentaje()
            archivo_str = " con archivo adjunto" if entrega.guia_file else ""
            registrar_trazabilidad(
                project,
                "Despacho Parcial",
                f"Se registró despacho con Guía N° {entrega.guia_despacho} ({entrega.get_estado_display()}){archivo_str}. Detalle: {entrega.cantidad_entregada}",
                request.user
            )
            messages.success(request, f'Guía {entrega.guia_despacho} registrada exitosamente.')
        else:
            messages.error(request, f'Error al registrar entrega: {form.errors}')
    return redirect('project_detail', numero_oc=numero_oc)


@login_required
def add_fmr(request, numero_oc):
    if request.method == 'POST':
        project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
        form = FMRForm(request.POST, request.FILES)
        if form.is_valid():
            fmr = form.save(commit=False)
            fmr.orden_compra = project
            fmr.save()
            archivo_str = " con archivo adjunto" if fmr.registro_file else ""
            registrar_trazabilidad(
                project,
                "Vinculación de FMR",
                f"Se vinculó el registro FMR N° {fmr.fmr_code}{archivo_str} (Cotización: {fmr.cotizacion or 'Sin cotización'})",
                request.user
            )
            messages.success(request, f'FMR {fmr.fmr_code} vinculado al proyecto.')
        else:
            messages.error(request, f'Error al crear FMR: {form.errors}')
    return redirect('project_detail', numero_oc=numero_oc)


@login_required
def add_item(request, numero_oc):
    if request.method == 'POST':
        project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
        form = ItemOCForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.orden_compra = project
            item.save()
            registrar_trazabilidad(
                project,
                "Item Agregado",
                f"Se agregó el item {item.linea}: {item.descripcion} (Cantidad: {item.cantidad} {item.unidad}, Precio Unitario: ${item.precio_unitario:,.0f})",
                request.user
            )
            messages.success(request, f'Item {item.linea} agregado exitosamente.')
        else:
            messages.error(request, f'Error al agregar item: {form.errors}')
    return redirect('project_detail', numero_oc=numero_oc)
@login_required
def cost_center_overview(request):
    projects_with_costs = OrdenCompra.objects.annotate(
        costs_total=Sum('costos__monto')
    ).order_by('-valor_total')

    summary_list = []
    total_budget = Decimal('0.00')
    total_expenses = Decimal('0.00')

    for p in projects_with_costs:
        budget = p.valor_total or Decimal('0.00')
        expenses = p.costs_total or Decimal('0.00')
        margin = budget - expenses
        margin_pct = float(margin / budget * 100) if budget > 0 else 0
        summary_list.append({
            'project': p, 'budget': budget,
            'expenses': expenses, 'margin': margin,
            'margin_pct': round(margin_pct, 2),
        })
        total_budget += budget
        total_expenses += expenses

    overall_margin = total_budget - total_expenses
    overall_margin_pct = float(overall_margin / total_budget * 100) if total_budget > 0 else 0

    categories_breakdown = Costo.objects.values('categoria').annotate(
        total=Sum('monto'), count=Count('id')
    ).order_by('-total')

    context = {
        'summary_list': summary_list,
        'total_budget': total_budget,
        'total_expenses': total_expenses,
        'overall_margin': overall_margin,
        'overall_margin_pct': round(overall_margin_pct, 2),
        'categories_breakdown': categories_breakdown,
    }
    return render(request, 'core/cost_center_overview.html', context)


def _run_excel_import(control_source, fmr_source, clear_db=False):
    if clear_db:
        Entrega.objects.all().delete()
        FMR.objects.all().delete()
        Costo.objects.all().delete()
        OrdenCompra.objects.all().delete()

    def clean_val(val, default=""):
        if pd.isna(val) or val is None:
            return default
        if isinstance(val, str):
            return val.strip()
        return str(val)

    def clean_decimal(val):
        if pd.isna(val) or val is None:
            return None
        try:
            return float(str(val).replace("$", "").replace(" ", "").replace(",", ""))
        except ValueError:
            return None

    def clean_int(val):
        if pd.isna(val) or val is None:
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    def clean_date(val):
        if pd.isna(val) or val is None:
            return None
        if hasattr(val, 'date'):
            return val.date()
        try:
            s = str(val).strip()
            if not s or s.lower() == 'nan':
                return None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
        except Exception:
            pass
        return None

    # Load Control OC
    df_oc = pd.read_excel(control_source, sheet_name="Control OC")
    
    col_map = {}
    for c in df_oc.columns:
        c_clean = str(c).strip().upper().replace(' ', '').replace('\ufffd', '')
        if 'N' in c_clean and 'OC' in c_clean:
            col_map[c] = 'N_OC'
        elif 'CLIENTE' in c_clean:
            col_map[c] = 'CLIENTE'
        elif 'FECHA' in c_clean and 'OC' in c_clean:
            col_map[c] = 'FECHA_OC'
        elif 'PROYECTO' in c_clean:
            col_map[c] = 'PROYECTO'
        elif 'DESCRIP' in c_clean:
            col_map[c] = 'DESCRIPCION'
        elif 'VALOR' in c_clean:
            col_map[c] = 'VALOR_TOTAL'
        elif 'TIEMPO' in c_clean:
            col_map[c] = 'TIEMPO_FABRICACION'
        elif 'COMPROMISO' in c_clean:
            col_map[c] = 'FECHA_COMPROMISO'
        elif 'ESTADO' in c_clean:
            col_map[c] = 'ESTADO'
        elif 'PORCENTAJE' in c_clean or '%' in c_clean:
            col_map[c] = 'PORCENTAJE_ENTREGADO'
        elif 'ULTIMA' in c_clean or 'LTIMA' in c_clean:
            col_map[c] = 'FECHA_ULTIMA_ENTREGA'
        elif 'RESTANTES' in c_clean:
            col_map[c] = 'DIAS_RESTANTES'
        elif 'PRIORIDAD' in c_clean:
            col_map[c] = 'PRIORIDAD'
        elif 'GU' in c_clean and 'DESPACHO' in c_clean:
            col_map[c] = 'GUIA_DESPACHO_RESUMEN'
        elif 'FACTURA' in c_clean and 'FECHA' in c_clean:
            col_map[c] = 'FECHA_FACTURA'
        elif 'FACTURA' in c_clean:
            col_map[c] = 'FACTURA_RESUMEN'
        elif 'OBSERVACION' in c_clean:
            col_map[c] = 'OBSERVACIONES'
        elif c_clean == 'OC':
            col_map[c] = 'OC_LINK'
        elif c_clean == 'FMR':
            col_map[c] = 'FMR_LINK'
        elif c_clean == 'PLANO':
            col_map[c] = 'PLANO_LINK'
        elif c_clean == 'EXCEL':
            col_map[c] = 'EXCEL_LINK'
        elif c_clean == 'DOSSIER':
            col_map[c] = 'DOSSIER_LINK'

    df_oc.rename(columns=col_map, inplace=True)

    created_ocs = 0
    for _, row in df_oc.iterrows():
        oc_num = clean_val(row.get("N_OC"))
        if not oc_num or oc_num.lower() == 'nan':
            continue
        pct_val = row.get("PORCENTAJE_ENTREGADO")
        try:
            pct = float(pct_val)
            porcentaje = pct * 100 if pct <= 1.0 else pct
        except (TypeError, ValueError):
            porcentaje = 0.0

        oc_link = clean_val(row.get("OC_LINK"))
        fmr_link = clean_val(row.get("FMR_LINK"))
        plano_link = clean_val(row.get("PLANO_LINK"))
        excel_link = clean_val(row.get("EXCEL_LINK"))
        dossier_link = clean_val(row.get("DOSSIER_LINK"))

        OrdenCompra.objects.update_or_create(
            numero_oc=oc_num,
            defaults={
                'cliente': clean_val(row.get("CLIENTE"), default="Desconocido"),
                'fecha_oc': clean_date(row.get("FECHA_OC")),
                'proyecto': clean_val(row.get("PROYECTO")),
                'descripcion': clean_val(row.get("DESCRIPCION")),
                'valor_total': clean_decimal(row.get("VALOR_TOTAL")),
                'tiempo_fabricacion': clean_int(row.get("TIEMPO_FABRICACION")),
                'fecha_compromiso': clean_date(row.get("FECHA_COMPROMISO")),
                'estado': clean_val(row.get("ESTADO"), default="En proceso"),
                'porcentaje_entregado': porcentaje,
                'fecha_ultima_entrega': clean_date(row.get("FECHA_ULTIMA_ENTREGA")),
                'dias_restantes': clean_int(row.get("DIAS_RESTANTES")),
                'prioridad': clean_val(row.get("PRIORIDAD")),
                'guia_despacho_resumen': clean_val(row.get("GUIA_DESPACHO_RESUMEN")),
                'factura_resumen': clean_val(row.get("FACTURA_RESUMEN")),
                'fecha_factura': clean_date(row.get("FECHA_FACTURA")),
                'observaciones': clean_val(row.get("OBSERVACIONES")),
                'oc_link': oc_link if oc_link.startswith("http") else None,
                'fmr_link': fmr_link if fmr_link.startswith("http") else None,
                'plano_link': plano_link if plano_link.startswith("http") else None,
                'excel_link': excel_link if excel_link.startswith("http") else None,
                'dossier_link': dossier_link if dossier_link.startswith("http") else None,
            }
        )
        created_ocs += 1

    df_e = pd.read_excel(control_source, sheet_name="Entregas")
    
    col_map_entregas = {}
    for c in df_e.columns:
        c_clean = str(c).strip().upper().replace(' ', '').replace('\ufffd', '')
        if 'N' in c_clean and 'OC' in c_clean:
            col_map_entregas[c] = 'N_OC'
        elif 'FECHA' in c_clean:
            col_map_entregas[c] = 'FECHA_ENTREGA'
        elif 'GU' in c_clean:
            col_map_entregas[c] = 'GUIA_DESPACHO'
        elif 'CANTIDAD' in c_clean:
            col_map_entregas[c] = 'CANTIDAD_ENTREGADA'
        elif 'OBSERVACION' in c_clean:
            col_map_entregas[c] = 'OBSERVACIONES'
        elif 'ESTADO' in c_clean:
            col_map_entregas[c] = 'ESTADO'

    df_e.rename(columns=col_map_entregas, inplace=True)

    created_e = 0
    for _, row in df_e.iterrows():
        oc_num = clean_val(row.get("N_OC"))
        if not oc_num or oc_num.lower() == 'nan':
            continue
        oc, _ = OrdenCompra.objects.get_or_create(
            numero_oc=oc_num,
            defaults={'cliente': "FLUOR SALFA LTDA", 'descripcion': "Generado desde Entregas"}
        )
        raw_estado = clean_val(row.get("ESTADO")).upper()
        if 'INCOMPLETA' in raw_estado:
            estado = 'INCOMPLETA'
        elif 'FACTURADO' in raw_estado:
            estado = 'FACTURADO'
        else:
            estado = 'COMPLETA'
        Entrega.objects.create(
            orden_compra=oc,
            fecha_entrega=clean_date(row.get("FECHA_ENTREGA")),
            guia_despacho=clean_val(row.get("GUIA_DESPACHO")),
            cantidad_entregada=clean_val(row.get("CANTIDAD_ENTREGADA")),
            observaciones=clean_val(row.get("OBSERVACIONES")),
            estado=estado,
        )
        created_e += 1

    df_fmr = pd.read_excel(fmr_source, sheet_name="Hoja1", header=3)
    
    col_map_fmr = {}
    for c in df_fmr.columns:
        c_clean = str(c).strip().upper().replace(' ', '').replace('\ufffd', '')
        if c_clean == 'FMR':
            col_map_fmr[c] = 'FMR_CODE'
        elif 'FECHA' in c_clean:
            col_map_fmr[c] = 'FECHA'
        elif 'COTIZACION' in c_clean or 'COTIZACI' in c_clean:
            col_map_fmr[c] = 'COTIZACION'
        elif 'ORDEN' in c_clean or 'COMPRA' in c_clean or 'OC' in c_clean:
            col_map_fmr[c] = 'N_OC'
        elif 'GUIA' in c_clean or 'GUA' in c_clean:
            col_map_fmr[c] = 'GUIA_DESPACHO'
        elif 'FACTURA' in c_clean:
            col_map_fmr[c] = 'FACTURA'
        elif 'REGISTRO' in c_clean:
            col_map_fmr[c] = 'REGISTRO_LINK'

    df_fmr.rename(columns=col_map_fmr, inplace=True)

    created_fmrs = 0
    for _, row in df_fmr.iterrows():
        fmr_code = clean_val(row.get("FMR_CODE"))
        if not fmr_code or fmr_code.lower() == 'nan':
            continue
        oc_num = clean_val(row.get("N_OC"))
        oc = None
        if oc_num and oc_num.lower() != 'nan':
            oc, _ = OrdenCompra.objects.get_or_create(
                numero_oc=oc_num.strip(),
                defaults={'cliente': "FLUOR SALFA LTDA", 'descripcion': f"Generado desde FMR {fmr_code}"}
            )
        registro_link = clean_val(row.get("REGISTRO_LINK"))
        FMR.objects.update_or_create(
            fmr_code=fmr_code,
            defaults={
                'orden_compra': oc,
                'fecha': clean_date(row.get("FECHA")),
                'cotizacion': clean_val(row.get("COTIZACION")),
                'guia_despacho': clean_val(row.get("GUIA_DESPACHO")),
                'factura': clean_val(row.get("FACTURA")),
                'registro_link': registro_link if registro_link.startswith("http") else None,
            }
        )
        created_fmrs += 1

    # Recalculate progress
    for oc in OrdenCompra.objects.all():
        oc.recalcular_porcentaje()

    return {'ocs': created_ocs, 'deliveries': created_e, 'fmrs': created_fmrs}

@login_required
def import_data(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        clear_db = request.POST.get('clear_db') == 'true'

        if action == 'local':
            control_source = r"c:\Users\Coalfa\Desktop\FLUOR\Control_Ordenes_Compra_Maestranza.xlsx"
            fmr_source = r"c:\Users\Coalfa\Desktop\FLUOR\FLUOR FMR.xlsx"
            if not os.path.exists(control_source) or not os.path.exists(fmr_source):
                messages.error(request, "No se encontraron los archivos locales.")
                return render(request, 'core/import_data.html')
        elif action == 'upload':
            control_source = request.FILES.get('control_file')
            fmr_source = request.FILES.get('fmr_file')
            if not control_source or not fmr_source:
                messages.error(request, "Debe subir ambos archivos Excel.")
                return render(request, 'core/import_data.html')
        else:
            messages.error(request, "Acción no reconocida.")
            return render(request, 'core/import_data.html')

        try:
            results = _run_excel_import(control_source, fmr_source, clear_db=clear_db)
            messages.success(
                request,
                f"✅ Sincronización exitosa — {results['ocs']} OCs, "
                f"{results['deliveries']} Despachos, {results['fmrs']} FMRs importados."
            )
        except Exception as e:
            messages.error(request, f"Error durante la sincronización: {e}")

        return redirect('project_list')

    return render(request, 'core/import_data.html')


# ──────────────────────────────────────────────────────────────────────────────
# PACKING LIST
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def add_packing_item(request, numero_oc, entrega_id):
    orden_compra = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
    entrega = get_object_or_404(Entrega, id=entrega_id, orden_compra=orden_compra)

    if request.method == 'POST':
        form = PackingListItemForm(request.POST, orden_compra=orden_compra)
        if form.is_valid():
            packing_item = form.save(commit=False)
            packing_item.entrega = entrega
            packing_item.save()  # triggers ItemOC.cantidad_entregada + OC % recalc

            registrar_trazabilidad(
                orden_compra=orden_compra,
                accion="Ítem Despachado (Packing List)",
                detalle=(
                    f"Ítem: '{packing_item.item_oc.descripcion}' — "
                    f"Cant: {packing_item.cantidad} | "
                    f"Bulto: {packing_item.numero_bulto or 'N/A'} | "
                    f"Guía: {entrega.guia_despacho or 'S/N'}"
                ),
                usuario=request.user
            )
            messages.success(request, "✅ Ítem añadido al Packing List del despacho.")
        else:
            messages.error(request, f"Error al añadir ítem: {form.errors}")

    return redirect('project_detail', numero_oc=numero_oc)


@login_required
def delete_packing_item(request, numero_oc, item_id):
    orden_compra = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
    packing_item = get_object_or_404(
        PackingListItem, id=item_id, entrega__orden_compra=orden_compra
    )

    registrar_trazabilidad(
        orden_compra=orden_compra,
        accion="Eliminar Ítem Packing List",
        detalle=(
            f"Se eliminó '{packing_item.item_oc.descripcion}' del despacho "
            f"guía {packing_item.entrega.guia_despacho or 'S/N'}. "
            f"Cantidad: {packing_item.cantidad}."
        ),
        usuario=request.user
    )
    packing_item.delete()  # triggers ItemOC.cantidad_entregada + OC % recalc
    messages.success(request, "🗑️ Ítem de Packing List eliminado.")
    return redirect('project_detail', numero_oc=numero_oc)


# ──────────────────────────────────────────────────────────────────────────────
# DETAILED COSTS ACTIONS (POST only)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def add_cost_material(request, numero_oc):
    if request.method == 'POST':
        project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
        form = CostoMaterialForm(request.POST)
        if form.is_valid():
            mat = form.save(commit=False)
            mat.orden_compra = project
            mat.save()
            
            registrar_trazabilidad(
                project,
                "Compra de Material",
                f"Se compró '{mat.producto}' (Cant: {mat.cantidad} | Unit: ${mat.valor_unitario:,.0f} | Total: ${mat.total:,.0f}) de {mat.proveedor or 'S/P'}.",
                request.user
            )
            messages.success(request, f"✅ Material '{mat.producto}' registrado exitosamente.")
        else:
            messages.error(request, f"Error al registrar material: {form.errors}")
    return redirect('project_detail', numero_oc=numero_oc)


@login_required
def delete_cost_material(request, numero_oc, item_id):
    project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
    mat = get_object_or_404(CostoMaterial, id=item_id, orden_compra=project)
    
    registrar_trazabilidad(
        project,
        "Eliminación de Material",
        f"Se eliminó registro de compra de '{mat.producto}' por ${mat.total:,.0f}.",
        request.user
    )
    mat.delete()
    messages.success(request, "🗑️ Registro de material eliminado.")
    return redirect('project_detail', numero_oc=numero_oc)


@login_required
def add_cost_mano_obra(request, numero_oc):
    if request.method == 'POST':
        project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
        form = CostoManoObraForm(request.POST)
        if form.is_valid():
            mo = form.save(commit=False)
            mo.orden_compra = project
            mo.save()
            
            registrar_trazabilidad(
                project,
                "Costo de Mano de Obra",
                f"Se registró '{mo.nombre_cargo}' (Trabajadores: {mo.cantidad_trabajadores} | Horas Totales: {mo.horas_totales} | Total: ${mo.total:,.0f}).",
                request.user
            )
            messages.success(request, f"✅ Mano de Obra para '{mo.nombre_cargo}' registrada exitosamente.")
        else:
            messages.error(request, f"Error al registrar mano de obra: {form.errors}")
    return redirect('project_detail', numero_oc=numero_oc)


@login_required
def delete_cost_mano_obra(request, numero_oc, item_id):
    project = get_object_or_404(OrdenCompra, numero_oc=numero_oc)
    mo = get_object_or_404(CostoManoObra, id=item_id, orden_compra=project)
    
    registrar_trazabilidad(
        project,
        "Eliminación de Mano de Obra",
        f"Se eliminó registro de mano de obra de '{mo.nombre_cargo}' por ${mo.total:,.0f}.",
        request.user
    )
    mo.delete()
    messages.success(request, "🗑️ Registro de mano de obra eliminado.")
    return redirect('project_detail', numero_oc=numero_oc)
