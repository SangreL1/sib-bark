from django.urls import path
from . import views

urlpatterns = [
    path('', views.rrhh_dashboard, name='rrhh_dashboard_root'),
    path('dashboard/', views.rrhh_dashboard, name='rrhh_dashboard'),
    path('empleados/', views.empleado_list, name='empleado_list'),
    path('empleado/nuevo/', views.empleado_create, name='empleado_create'),
    path('empleado/<int:empleado_id>/', views.empleado_detail, name='empleado_detail'),
    path('empleado/<int:empleado_id>/eliminar/', views.empleado_delete, name='empleado_delete'),
    path('empleado/<int:empleado_id>/generar-liq/', views.liquidacion_generar, name='liquidacion_generar'),
    path('empleado/<int:empleado_id>/asistencia/', views.asistencia_mensual, name='asistencia_mensual'),
    path('empleado/<int:empleado_id>/asistencia/llenar/', views.asistencia_mensual_llena, name='asistencia_mensual_llena'),
    path('asistencia/masiva/', views.asistencia_masiva, name='asistencia_masiva'),
    path('empleado/<int:empleado_id>/liquidacion/<int:mes>/<int:anio>/', views.liquidacion_pdf, name='liquidacion_pdf'),
    path('configuracion/', views.configuracion_legal, name='configuracion_legal'),
]
