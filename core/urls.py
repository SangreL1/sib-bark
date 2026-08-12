from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Main screens
    path('', views.project_list, name='project_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('despachos/', views.despachos_list, name='despachos_list'),

    # Search
    path('buscar/', views.search, name='search'),

    # OC CRUD
    # OC CRUD (creation only here, edit/delete moved to bottom to avoid path greediness)
    path('proyectos/nuevo/', views.oc_create, name='oc_create'),
    path('proyecto/<path:numero_oc>/agregar-costo/', views.add_cost, name='add_cost'),
    
    # Costos Detallados (Materiales y Mano de Obra)
    path('proyecto/<path:numero_oc>/agregar-material/', views.add_cost_material, name='add_cost_material'),
    path('proyecto/<path:numero_oc>/material/<int:item_id>/eliminar/', views.delete_cost_material, name='delete_cost_material'),
    path('proyecto/<path:numero_oc>/agregar-mano-obra/', views.add_cost_mano_obra, name='add_cost_mano_obra'),
    path('proyecto/<path:numero_oc>/mano-obra/<int:item_id>/eliminar/', views.delete_cost_mano_obra, name='delete_cost_mano_obra'),

    path('proyecto/<path:numero_oc>/agregar-entrega/', views.add_entrega, name='add_entrega'),
    path('proyecto/<path:numero_oc>/agregar-fmr/', views.add_fmr, name='add_fmr'),
    path('proyecto/<path:numero_oc>/agregar-item/', views.add_item, name='add_item'),
    path('proyecto/<path:numero_oc>/editar-item/<int:item_id>/', views.edit_item, name='edit_item'),
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/agregar-packing-item/', views.add_packing_item, name='add_packing_item'),
    path('proyecto/<path:numero_oc>/packing-item/<int:item_id>/editar/', views.edit_packing_item, name='edit_packing_item'),
    path('proyecto/<path:numero_oc>/packing-item/<int:item_id>/eliminar/', views.delete_packing_item, name='delete_packing_item'),

    # Cost center
    path('centro-costos/', views.cost_center_overview, name='cost_center_overview'),

    # Rendicion y Costeo Detallado
    path('proyecto/<path:numero_oc>/rendicion/', views.project_rendicion, name='project_rendicion'),
    path('proyecto/<path:numero_oc>/exportar-bom/', views.export_bom_csv, name='export_bom_csv'),
    path('proyecto/<path:numero_oc>/exportar-rendicion/', views.export_rendicion_csv, name='export_rendicion_csv'),
    path('proyecto/<path:numero_oc>/agregar-materia-prima/', views.add_materia_prima, name='add_materia_prima'),
    path('proyecto/<path:numero_oc>/materia-prima/<int:item_id>/eliminar/', views.delete_materia_prima, name='delete_materia_prima'),
    path('proyecto/<path:numero_oc>/agregar-mo-detallada/', views.add_mano_obra_detallada, name='add_mo_detallada'),
    path('proyecto/<path:numero_oc>/mo-detallada/<int:item_id>/eliminar/', views.delete_mano_obra_detallada, name='delete_mo_detallada'),

    # Entrega Detalle y Packing List
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/', views.entrega_detail, name='entrega_detail'),
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/crear-packing-list/', views.create_packing_list, name='create_packing_list'),
    path('packing-list/<int:packing_list_id>/pdf/', views.generate_packing_list_pdf, name='generate_packing_list_pdf'),
    path('packing-list/<int:packing_list_id>/excel/', views.export_packing_list_excel, name='export_packing_list_excel'),
    path('packing-list/<int:packing_list_id>/eliminar/', views.delete_packing_list, name='delete_packing_list'),

    # Guía de Despacho (modelo estructurado)
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/crear-guia/', views.guia_create, name='guia_create'),
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/guia/', views.guia_detail, name='guia_detail'),
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/guia/pdf/', views.guia_pdf, name='guia_pdf'),
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/guia/item/<int:item_id>/eliminar/', views.guia_item_delete, name='guia_item_delete'),
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/guia-packing-combinado/', views.guia_packing_combinado_pdf, name='guia_packing_combinado_pdf'),

    # Cotización
    path('cotizaciones/', views.cotizacion_list, name='cotizacion_list'),
    path('cotizaciones/nueva/', views.cotizacion_create, name='cotizacion_create'),
    path('cotizaciones/<int:cotizacion_id>/', views.cotizacion_detail, name='cotizacion_detail'),
    path('cotizaciones/<int:cotizacion_id>/pdf/', views.cotizacion_pdf, name='cotizacion_pdf'),
    path('cotizaciones/<int:cotizacion_id>/item/<int:item_id>/eliminar/', views.cotizacion_item_delete, name='cotizacion_item_delete'),

    # OC base routes (placed here so <path:numero_oc> doesn't swallow more specific routes)
    path('proyecto/<path:numero_oc>/editar/', views.oc_edit, name='oc_edit'),
    path('proyecto/<path:numero_oc>/eliminar/', views.oc_delete, name='oc_delete'),
    path('proyecto/<path:numero_oc>/', views.project_detail, name='project_detail'),

    # Import y Herramientas API
    path('importar/', views.import_data, name='import_data'),
    path('api/analizar-documento/', views.api_analizar_documento, name='api_analizar_documento'),

    # ══════════════════════════════════════════════════════════════════════════
    # PORTAL OC CLIENTES — Módulo B2B que reemplaza ICONSTRUYE
    # ══════════════════════════════════════════════════════════════════════════

    # API utilitarios
    path('api/validar-rut/', views.api_validar_rut, name='api_validar_rut'),

    # Portal Cliente (acceso externo)
    path('portal/', views.portal_dashboard, name='portal_dashboard'),
    path('portal/registro/', views.portal_registro, name='portal_registro'),
    path('portal/login/', views.portal_login, name='portal_login'),
    path('portal/oc/nueva/', views.portal_nueva_oc, name='portal_nueva_oc'),
    path('portal/oc/<int:oc_id>/', views.portal_oc_detail, name='portal_oc_detail'),

    # Panel Interno Bark (solo staff)
    path('oc-clientes/', views.oc_clientes_bandeja, name='oc_clientes_bandeja'),
    path('oc-clientes/<int:oc_id>/aceptar/', views.oc_cliente_aceptar, name='oc_cliente_aceptar'),
    path('oc-clientes/<int:oc_id>/rechazar/', views.oc_cliente_rechazar, name='oc_cliente_rechazar'),
    path('oc-clientes/accesos/', views.solicitudes_acceso_lista, name='solicitudes_acceso_lista'),
    path('oc-clientes/accesos/<int:perfil_id>/aprobar/', views.aprobar_cliente, name='aprobar_cliente'),
    path('oc-clientes/accesos/staff/<int:user_id>/aprobar/', views.aprobar_staff, name='aprobar_staff'),
    path('oc-clientes/accesos/<int:perfil_id>/rechazar/', views.rechazar_cliente, name='rechazar_cliente'),
    path('oc-clientes/accesos/<int:perfil_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('oc-clientes/accesos/<int:perfil_id>/bloquear/', views.bloquear_cliente, name='bloquear_cliente'),
    path('oc-clientes/accesos/<int:perfil_id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    
    # URLS para gestión de STAFF (empleados)
    path('oc-clientes/accesos/staff/<int:user_id>/editar/', views.editar_staff, name='editar_staff'),
    path('oc-clientes/accesos/staff/<int:user_id>/bloquear/', views.bloquear_staff, name='bloquear_staff'),
    path('oc-clientes/accesos/staff/<int:user_id>/eliminar/', views.eliminar_staff, name='eliminar_staff'),
    
    path('oc-clientes/configuracion/', views.oc_clientes_config, name='oc_clientes_config'),
]
