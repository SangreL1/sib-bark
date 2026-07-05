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

    # Search
    path('buscar/', views.search, name='search'),

    # OC CRUD
    path('proyectos/nuevo/', views.oc_create, name='oc_create'),
    path('proyecto/<path:numero_oc>/editar/', views.oc_edit, name='oc_edit'),
    path('proyecto/<path:numero_oc>/agregar-costo/', views.add_cost, name='add_cost'),
    
    # Costos Detallados (Materiales y Mano de Obra)
    path('proyecto/<path:numero_oc>/agregar-material/', views.add_cost_material, name='add_cost_material'),
    path('proyecto/<path:numero_oc>/material/<int:item_id>/eliminar/', views.delete_cost_material, name='delete_cost_material'),
    path('proyecto/<path:numero_oc>/agregar-mano-obra/', views.add_cost_mano_obra, name='add_cost_mano_obra'),
    path('proyecto/<path:numero_oc>/mano-obra/<int:item_id>/eliminar/', views.delete_cost_mano_obra, name='delete_cost_mano_obra'),

    path('proyecto/<path:numero_oc>/agregar-entrega/', views.add_entrega, name='add_entrega'),
    path('proyecto/<path:numero_oc>/agregar-fmr/', views.add_fmr, name='add_fmr'),
    path('proyecto/<path:numero_oc>/agregar-item/', views.add_item, name='add_item'),
    path('proyecto/<path:numero_oc>/entrega/<int:entrega_id>/agregar-packing-item/', views.add_packing_item, name='add_packing_item'),
    path('proyecto/<path:numero_oc>/packing-item/<int:item_id>/eliminar/', views.delete_packing_item, name='delete_packing_item'),
    path('proyecto/<path:numero_oc>/', views.project_detail, name='project_detail'),

    # Cost center
    path('centro-costos/', views.cost_center_overview, name='cost_center_overview'),

    # Import
    path('importar/', views.import_data, name='import_data'),
]
