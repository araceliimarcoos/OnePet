from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    
    # ── Página de inicio (landing) ──────────────
    path('', views.inicio, name='inicio'),
    
    path('api/citas/', views.api_citas, name='api_citas'),
    
    # ── Login / Logout ──────────────────────────
    path('login/',  auth_views.LoginView.as_view(template_name='login.html'),  name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'),         name='logout'),
    
    #Resto del app
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mascotas/', views.mascotas, name='mascotas'),
    
    # Esta es para 'ver perfil' son los detalles y asi
    path('mascotas/mascotas_detalles/', views.detalles_mascota, name='detalles_mascota'), 
    path('propietarios/propietarios_detalles/', views.detalles_propietario, name='detalles_propietario'),
    
    path('propietarios/', views.propietarios, name='propietarios'),
    path('citas/', views.citas, name='citas'),
    
    path('consultas/', views.consultas, name='consultas'),
    path('consultas/iniciar_consulta/', views.iniciar_consulta, name='iniciar_consulta'),   # Iniciar consulta
    path('citas/buscar/', views.buscar_citas, name='buscar_citas'),
    
    path('hospitalizacion/', views.hospitalizacion, name='hospitalizacion'),
    path('pagos/', views.pagos, name='pagos'),
    path('servicios/', views.servicios, name='servicios'),
    path('catalogo/', views.servicios, name='catalogo'),
    path('medicamentos/', views.medicamentos, name='medicamentos'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('especies/', views.especies, name='especies'),
    path('especies/<str:clave_especie>/', views.razas, name='razas'),
    
    
    path('personal/', views.personal, name='personal'),
    path('reportes/', views.reportes, name='reportes'),
    
    #Estos son para las ventanitas
    path('mascotas/nueva/', views.nueva_mascota, name='nueva_mascota'),
    path('propietarios/nuevo/', views.nuevo_propietario, name='nuevo_propietario'),
]