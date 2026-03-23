# web/views.py
#####################################################################################
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
# Importa solo los que necesites para la lista por ahora:
from .models import Mascota, Propietario, Especie, Raza
#####################################################################################
from django.core.paginator import Paginator
from django.db.models import Q
####################################################################################
def inicio(request):
    """Página de inicio pública (landing page)."""
    if request.user.is_authenticated:
        return redirect('dashboard')          # si ya inició sesión, ir directo al panel
    return render(request, 'inicio.html')

@login_required
def api_citas(request):
    # Cuando tengas modelos reales, harías:
    # citas = Cita.objects.all()
    # y construirías la lista desde la BD

    eventos = [
        {
            "id":    1,
            "title": "Consulta - Firulais",
            "start": "2026-03-13T10:00:00",
            "end":   "2026-03-13T10:30:00",
            "color": "#43C0B0",          # color opcional por evento
        },
        {
            "id":    2,
            "title": "Cirugía - Max",
            "start": "2026-03-14T09:00:00",
            "end":   "2026-03-14T11:00:00",
            "color": "#e74c3c",
        },
    ]
    return JsonResponse(eventos, safe=False)


@login_required
def dashboard (request):
    return render(request, 'dashboard.html', { 'seccion_activa': 'dashboard' })
############################################################################################
from django.core.paginator import Paginator
from django.db.models import Q # Importante para búsquedas complejas



#################################################################################3
@login_required

def mascotas(request):

    contexto = {

        'seccion_activa': 'mascotas',

        'mascotas': Mascota.objects.select_related('propietario', 'especie', 'raza').all(),

        'especies': Especie.objects.all().order_by('nombre'),
        'razas': Raza.objects.all().order_by('nombre'),

        'total_conteo': Mascota.objects.count()

    }

    return render(request, 'mascotas/mascotas_lista.html', contexto)

###############################################################################################
@login_required
def detalles_mascota(request):
    return render(request, 'mascotas/mascotas_detalles.html', { 'seccion_activa': 'mascotas' })
    
@login_required
def propietarios(request):
    return render(request, 'propietarios/propietarios_lista.html', { 'seccion_activa': 'propietarios'})

@login_required
def detalles_propietario(request):
    return render(request, 'propietarios/propietarios_detalles.html', { 'seccion_activa': 'propietarios'})

@login_required
def citas(request):
    return render(request, 'citas/citas_lista.html', { 'seccion_activa': 'citas'})

@login_required
def consultas(request):
    return render(request, 'consultas/consultas_lista.html', { 'seccion_activa': 'consultas' })

@login_required
def iniciar_consulta(request):
    return render(request, 'consultas/consultas_inicio.html', {'seccion_activa': 'consultas'})

@login_required
def hospitalizacion(request):
    return render(request, 'hospitalizacion/hospitalizacion_lista.html', { 'seccion_activa': 'hospitalizacion' })

@login_required
def pagos(request):
    return render(request, 'pagos/pagos_lista.html', { 'seccion_activa': 'pagos' })

@login_required
def catalogo(request):
    return render(request, 'catalogo/catalogo_lista.html', { 'seccion_activa': 'catalogo' })
@login_required
def medicamentos(request):
    return render(request, 'medicamentos/medicamentos_lista.html', { 'seccion_activa': 'medicamentos' })

@login_required
def usuarios(request):
    return render(request, 'usuarios/usuarios_lista.html', { 'seccion_activa': 'usuarios' })

@login_required
def especies(request):
    return render(request, 'especies/especies_lista.html', { 'seccion_activa': 'especies' })

@login_required
def personal(request):
    return render(request, 'personal/personal_lista.html', { 'seccion_activa': 'personal' })

@login_required
def reportes(request):
    return render(request, 'reportes/reportes.html', { 'seccion_activa': 'reportes' })


# Estos son para las ventanitas o algo asi
def nueva_mascota(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        especie = request.POST.get('especie')
        raza = request.POST.get('raza')
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

def nuevo_propietario(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        especie = request.POST.get('apellido')
        raza = request.POST.get('correo')
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})
