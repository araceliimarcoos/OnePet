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
    path('mascotas/perfiles/<str:folio>/', views.detalles_mascota, name='detalles_mascota'), 
    path('propietarios/perfiles/<str:folio>/', views.propietarios_detalles, name='detalles_propietario'),
    
    path('propietarios/', views.propietarios, name='propietarios'),
    
    path('citas/', views.citas, name='citas'),
    path('citas/nueva/', views.nueva_cita, name='nueva_cita'),
    path('citas/<str:folio>/editar/', views.editar_cita, name='editar_cita'),
    
    path('consultas/', views.consultas, name='consultas'),
    path('consultas/<str:folio_cita>/iniciar/', views.iniciar_consulta,  name='iniciar_consulta'),
    path('consultas/<int:numero>/ver/',         views.ver_consulta,      name='ver_consulta'),
    path('consultas/<int:numero>/editar/',      views.editar_consulta,   name='editar_consulta'),
    path('citas/buscar/', views.buscar_citas, name='buscar_citas'),
    
    path('hospitalizacion/', views.hospitalizacion, name='hospitalizacion'),
    path('hospitalizacion/<int:consulta_numero>/iniciar/', views.iniciar_hospitalizacion,  name='iniciar_hospitalizacion'),
    path('hospitalizacion/<int:numero>/ver/',              views.ver_hospitalizacion,      name='ver_hospitalizacion'),
    path('hospitalizacion/<int:numero>/editar/',           views.editar_hospitalizacion,   name='editar_hospitalizacion'),
    path('hospitalizacion/<int:numero>/alta/',             views.dar_alta_hospitalizacion, name='dar_alta_hospitalizacion'),
    
    path('pagos/', views.pagos, name='pagos'),
    path('pagos/<int:codigo>/recibo/',  views.ver_recibo,         name='ver_recibo'),
    path('pagos/previsualizar/',        views.previsualizar_pago, name='previsualizar_pago'),
    path('pagos/confirmar/',            views.confirmar_pago,     name='confirmar_pago'),
    
    path('servicios/', views.servicios, name='servicios'),
    path('servicios/nuevo/', views.nuevo_servicio, name='nuevo_servicio'),
    
    path('medicamentos/', views.medicamentos, name='medicamentos'),
    path('medicamentos/nuevo/', views.nuevo_medicamento, name='nuevo_medicamento'),
    
    path('usuarios/', views.usuarios, name='usuarios'),
    
    path('especies/', views.especies, name='especies'),                     # para acceder a la lista de especies
    path('especies/nueva/', views.nueva_especie, name='nueva_especie'),     # para crear una nueva especie
    path('especies/razas/nueva/', views.nueva_raza, name='nueva_raza'),     # para crear una nueva raza
    path('especies/razas/<str:clave_especie>/', views.razas, name='razas'), # para acceder a la lista de razas
    
    path('personal/', views.personal, name='personal'),
    path('personal/nuevo/', views.nuevo_veterinario, name='nuevo_veterinario'),
    path('personal/especialidades/nueva/', views.nueva_especialidad, name='nueva_especialidad'),
    path('personal/<str:folio>/editar/', views.editar_veterinario, name='editar_veterinario'),
    path('personal/<str:folio>/baja/', views.baja_veterinario,   name='baja_veterinario'),
        
    path('reportes/', views.reportes, name='reportes'),
    
    #Estos son para las ventanitas
    path('mascotas/nueva/', views.nueva_mascota, name='nueva_mascota'),
    
    path('propietarios/nuevo/', views.nuevo_propietario, name='nuevo_propietario'), #Este es del modal
    path('propietarios/folio/', views.obtener_folio, name='obtener_folio'),#Este obtiene el folio
    path('propietarios/crear/', views.crear_propietario, name='crear_propietario')#Este es para crear uno nuevo
]