# web/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
# Importa solo los que necesites para la lista por ahora:
from .models import Mascota, Propietario, Especie, Raza, Servicio

from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Count
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
#------------------------------------------ MASCOTAS ------------------------------------------------#

@login_required
def mascotas(request):

    mascotas_list = Mascota.objects.select_related(
        'propietario', 'especie', 'raza'
    ).all()

    paginator = Paginator(mascotas_list, 15)  # 15 por página en cada tablita

    page_number = request.GET.get('page')
    mascotas = paginator.get_page(page_number)

    contexto = {
        'seccion_activa': 'mascotas',
        'mascotas': mascotas,  #  ahora es paginado
        'especies': Especie.objects.all().order_by('nombre'),
        'razas': Raza.objects.all().order_by('nombre'),
        'total_conteo': paginator.count  #  mejor que count()
    }

    return render(request, 'mascotas/mascotas_lista.html', contexto)
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
@login_required
def detalles_mascota(request):
    return render(request, 'mascotas/mascotas_detalles.html', { 'seccion_activa': 'mascotas' })

#------------------------------------------------------------ P R O P I E T A R I O S -----------------------------------------------------------------#

@login_required
def propietarios(request):

    query = request.GET.get('q')

    propietarios_list = Propietario.objects.prefetch_related(
        'telefono_set',
        'mascota_set'
    )


    if query:
        propietarios_list = propietarios_list.filter(
            Q(nombrepila__icontains=query) |
            Q(primerapellido__icontains=query) |
            Q(segundoapellido__icontains=query) |
            Q(folio__icontains=query)
        )

    paginator = Paginator(propietarios_list, 15)
    page_number = request.GET.get('page')
    propietarios = paginator.get_page(page_number)

    contexto = {
        'seccion_activa': 'propietarios',
        'propietarios': propietarios,
        'total_conteo': paginator.count,
        'query': query
    }

    return render(request, 'propietarios/propietarios_lista.html', contexto)
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
@login_required
def detalles_propietario(request):
    return render(request, 'propietarios/propietarios_detalles.html', { 'seccion_activa': 'propietarios'})

#------------------------------------------------------------------- C I T A S ---------------------------------------------------------------------#
@login_required
def citas(request):
    return render(request, 'citas/citas_lista.html', { 'seccion_activa': 'citas'})

#------------------------------------------------------------------ C O N S U L T A S ------------------------------------------------------------#

@login_required
def consultas(request):
    return render(request, 'consultas/consultas_lista.html', { 'seccion_activa': 'consultas' })

@login_required
def iniciar_consulta(request):
    return render(request, 'consultas/consultas_inicio.html', {'seccion_activa': 'consultas'})

#.................................................................... H O S P I T A LI Z A C I O N E S ...................................................................#
@login_required
def hospitalizacion(request):
    return render(request, 'hospitalizacion/hospitalizacion_lista.html', { 'seccion_activa': 'hospitalizacion' })

#............................................................................. P A G O S ..................................................................................#
@login_required
def pagos(request):
    return render(request, 'pagos/pagos_lista.html', { 'seccion_activa': 'pagos' })
#............................................................................ S E R V I C I O S ............................................................................#

from django.db.models import Q

@login_required
def servicios(request):

    query = request.GET.get('q')

    servicios_list = Servicio.objects.all()

    if query:
        servicios_list = servicios_list.filter(
            Q(nombre__icontains=query) |
            Q(clave__icontains=query) 
        )

    servicios_list = servicios_list.order_by('nombre')

    paginator = Paginator(servicios_list, 15)
    page_number = request.GET.get('page')
    servicios = paginator.get_page(page_number)

    contexto = {
        'seccion_activa': 'servicios',
        'servicios': servicios,
        'total_conteo': paginator.count,
        'query': query
    }

    return render(request, 'servicios/servicios_lista.html', contexto)
#------------------------------------------ PAGOS ------------------------------------------------------------#

@login_required
def medicamentos(request):
    return render(request, 'medicamentos/medicamentos_lista.html', { 'seccion_activa': 'medicamentos' })
#------------------------------------------ PAGOS ------------------------------------------------------------#

@login_required
def usuarios(request):
    return render(request, 'usuarios/usuarios_lista.html', { 'seccion_activa': 'usuarios' })
#------------------------------------------ ESPECIES ------------------------------------------------------------#

@login_required
def especies(request):
    
    especies_list = Especie.objects.annotate(
        total_mascotas=Count('mascota'),
        total_razas=Count('raza', distinct=True)
    ).order_by('nombre')
    
    especie_top = especies_list.order_by('-total_mascotas').first()
    
    contexto = {
        'seccion_activa': 'especies',
        'especies': especies_list,
        'total_especies': especies_list.count(),
        'especie_top': especie_top
    }
    
    
    return render(request, 'especies/especies_lista.html', contexto)

#------------------------------------------ RAZAS ------------------------------------------------------------#

@login_required
def razas(request, clave_especie):
    
    especie = get_object_or_404(Especie, clave=clave_especie)
    
    razas_list = Raza.objects.filter(especie=especie).annotate(
        total_mascotas=Count('mascota')
    ).order_by('nombre')
    
    contexto = {
        'seccion_activa': 'especies',
        'especie': especie,
        'razas': razas_list,
        'total_razas': razas_list.count(),
    }
    
    return render(request, 'especies/razas_lista.html', contexto)


#------------------------------------------ PAGOS ------------------------------------------------------------#

@login_required
def personal(request):
    return render(request, 'personal/personal_lista.html', { 'seccion_activa': 'personal' })
#------------------------------------------ PAGOS ------------------------------------------------------------#

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
