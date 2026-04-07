#..........................................................................................................................................................

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Mascota, Propietario, Especie, Raza, Servicio, Medicamento, Usuario, Veterinario, Recepcionista, Administrador, Cita, Hospitalizacion, SignosVitales, Especialidad, Telefono, Pago, Expediente, Consulta, Receta

from django.core.paginator import Paginator
from django.db.models import Q, Count
import re
import json
#........................................................................................................................................................

def inicio(request):
    """Página de inicio pública (landing page)."""
    if request.user.is_authenticated:
        return redirect('dashboard')          # si ya inició sesión, ir directo al panel
    return render(request, 'inicio.html')

@login_required
def api_citas(request):

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
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------- M A S C O T A S --------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
def detalles_mascota(request, folio):
    mascota = get_object_or_404(
        Mascota.objects.select_related('propietario', 'especie', 'raza','estado'), 
        folio=folio
    )
    telefonos = Telefono.objects.filter(propietario=mascota.propietario).first()
    hoy = timezone.now().date()
    anios = hoy.year - mascota.fechanacimiento.year
    meses = hoy.month - mascota.fechanacimiento.month
    
    if (hoy.month, hoy.day) < (mascota.fechanacimiento.month, mascota.fechanacimiento.day):
        anios -= 1
    if meses < 0:
        meses += 12

    if anios == 0:
        mascota.edad = f"{meses} mes{'es' if meses != 1 else ''}"
    else:
        mascota.edad = f"{anios} año{'s' if anios != 1 else ''}"

    # Expediente y historial
    expediente = Expediente.objects.filter(mascota=mascota).first()
    consultas = []
    if expediente:
        consultas = Consulta.objects.filter(
            expediente=expediente
        ).select_related('cita__veterinario').order_by('-numero')

    contexto = {
        'seccion_activa': 'mascotas',
        'mascota': mascota,
        'expediente': expediente,
        'consultas': consultas,
        'telefonos': telefonos
    }

    return render(request, 'mascotas/mascotas_detalles.html', contexto)


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------- P R O P I E T A R I O S --------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
    
    propietarios_list = propietarios_list.order_by('-folio')

    paginator = Paginator(propietarios_list, 10)
    page_number = request.GET.get('page')
    propietarios = paginator.get_page(page_number)

    contexto = {
        'seccion_activa': 'propietarios',
        'propietarios': propietarios,
        'total_conteo': paginator.count,
        'query': query
    }

    return render(request, 'propietarios/propietarios_lista.html', contexto)
# . . . . .  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .  . . . . . . . . . . . . . . . . . . . .

@login_required
def propietarios_detalles(request,folio):
    propietario = get_object_or_404(Propietario,folio=folio)
    telefonos = Telefono.objects.filter(propietario=propietario).first()
    mascotas = Mascota.objects.filter(propietario=propietario)
    citas = Cita.objects.filter(propietario=propietario).select_related('mascota', 'veterinario').order_by('-fecha')[:5]
    # Edades de las mascotas
    hoy = timezone.now().date()
    mascotas_con_edad = []
    for m in mascotas:
        anios = hoy.year - m.fechanacimiento.year
        if (hoy.month, hoy.day) < (m.fechanacimiento.month, m.fechanacimiento.day):
            anios -= 1
        m.edad = f"{anios} año{'s' if anios != 1 else ''}"
        mascotas_con_edad.append(m)

    contexto = {
        'seccion_activa': 'propietarios',
        'propietario': propietario,
        'telefonos': telefonos,
        'mascotas': mascotas,
        'mascotas_count': len(mascotas_con_edad),
        'citas': citas
    }

    return render(request, 'propietarios/propietarios_detalles.html', contexto)
    
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 

from django.db import transaction, IntegrityError
from .services import validar_datos, crear_propietario_db, generar_folio

def crear_propietario(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = request.POST.copy()

        with transaction.atomic():

            # VALIDACIÓN
            valido, error = validar_datos(data)
            if not valido:
                return JsonResponse({'ok': False, 'error': error})

            # CREACIÓN
            propietario = crear_propietario_db(data)

        return JsonResponse({
            'ok': True,
            'message': 'Propietario guardado correctamente',
            'id': propietario.folio
        })

    except IntegrityError:
        return JsonResponse({
            'ok': False,
            'error': 'El correo ya está registrado'
        })

    except ValueError as e:
        return JsonResponse({
            'ok': False,
            'error': str(e)
        })

    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': str(e)
        })
        
def obtener_folio(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)

    return JsonResponse({'folio': generar_folio()})

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------- C I T A S --------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required
def citas(request):
    query = request.GET.get('q', '').strip()

    citas_list = Cita.objects.select_related(
        'mascota__propietario',
        'mascota__raza__especie',
        'veterinario',
        'estado'
    ).order_by('-fecha', '-hora')

    if query:
        citas_list = citas_list.filter(
            Q(folio__icontains=query) |
            Q(mascota__nombre__icontains=query) |
            Q(propietario__primerapellido__icontains=query)
        )

    # Stats
    conteos = Cita.objects.values('estado__nombre').annotate(total=Count('folio'))
    stats = {item['estado__nombre']: item['total'] for item in conteos}

    # Paginación
    paginator = Paginator(citas_list, 15)
    page_number = request.GET.get('page')
    citas = paginator.get_page(page_number)

    contexto = {
        'seccion_activa': 'citas',
        'citas': citas,
        'stats': stats,
        'total_conteo': paginator.count,
        'query': query,
    }

    return render(request, 'citas/citas_lista.html', contexto)

#------------------------------------------------------------------ C O N S U L T A S ------------------------------------------------------------#

@login_required
def consultas(request):
    query = request.GET.get('q', '').strip()
    
    consultas_list = Consulta.objects.select_related(
        'cita__mascota__propietario'
    ).order_by('-numero')
    
    if query:
        consultas_list = consultas_list.filter(
            Q(numero__icontains=query) |
            Q(cita__mascota__nombre__icontains=query) |
            Q(cita__propietario__primerapellido__icontains=query)
        )
    
    # Paginación
    paginator = Paginator(consultas_list, 15)
    page_number = request.GET.get('page')
    consultas = paginator.get_page(page_number)
    
    contexto = {
        'seccion_activa': 'consultas',
        'consultas': consultas,
        'total_conteo': paginator.count,
    }
    
    return render(request, 'consultas/consultas_lista.html', contexto)

@login_required
def iniciar_consulta(request):
    return render(request, 'consultas/consultas_inicio.html', {'seccion_activa': 'consultas'})

@login_required
def buscar_citas(request):                  # Para la busqueda de citas en 'Iniciar consulta'
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    citas = Cita.objects.select_related(
        'mascota__propietario', 'veterinario'
    ).filter(
        Q(folio__icontains=query) |
        Q(mascota__nombre__icontains=query)
    ).values(
        'folio',
        'fecha',
        'hora',
        'motivo',
        'mascota__nombre',
        'mascota__propietario__nombrepila',
        'mascota__propietario__primerapellido',
        'veterinario__nombrepila',
        'veterinario__primerapellido',
        'estado__nombre',
    )[:6]  # ← menos resultados

    resultados = [
        {
            'folio':       c['folio'],
            'fecha':       c['fecha'].strftime('%d/%m/%Y'),
            'hora':        c['hora'].strftime('%H:%M'),
            'motivo':      c['motivo'],
            'mascota':     c['mascota__nombre'],
            'propietario': f"{c['mascota__propietario__nombrepila']} {c['mascota__propietario__primerapellido']}",
            'veterinario': f"{c['veterinario__nombrepila']} {c['veterinario__primerapellido']}",
            'estado':      c['estado__nombre'],
        }
        for c in citas
    ]

    return JsonResponse(resultados, safe=False)

#.................................................................... H O S P I T A LI Z A C I O N E S ...................................................................#
@login_required
def hospitalizacion(request):
    
    hoy = timezone.now().date()
    
    hosp_list = Hospitalizacion.objects.select_related(
        'veterinario',
        'estado',
        'expediente__mascota__propietario'
    ).order_by('-fechaingreso')
    
    # pa las stats
    activas = hosp_list.filter(fechaalta__isnull=True)    #  mascotas Hospitalizadas
    
    revisiones_ya_hechas_hoy = SignosVitales.objects.filter(fecha=hoy).values_list('hospitalizacion_id', flat=True)
    
    pendientes = activas.exclude(numero__in=revisiones_ya_hechas_hoy).count()
    
    altas_hoy = hosp_list.filter(fechaalta=hoy).count()
    
    

    contexto = {
        'seccion_activa':       'hospitalizacion',
        'hospitalizaciones':    hosp_list,
        'activas':              activas.count(),
        'admitidas_hoy':        activas.filter(fechaingreso=hoy).count(),     
        'pendientes':           pendientes,
        'altas_hoy':            altas_hoy,
        'total_conteo':         hosp_list.count(),
    }
    
    return render(request, 'hospitalizacion/hospitalizacion_lista.html', contexto)

#............................................................................. P A G O S ..................................................................................#
@login_required
def pagos(request):
    
    pagos_list = Pago.objects.select_related(
        'consulta__cita__mascota__propietario',
        'hospitalizacion'
    ).order_by('-fecha', '-hora')
    
    contexto = {
        'seccion_activa': 'pagos',
        'pagos': pagos_list,
    }
    
    return render(request, 'pagos/pagos_lista.html', contexto)

@login_required
def recibos(request):
    
    return render(request, 'pagos/pagos_recibo.html', { 'seccion_activa': 'pagos' })

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

from .services import validar_datos_servicio, crear_servicio_db
@require_POST
def nuevo_servicio(request):
    try:
        data = {
            'nombre': request.POST.get('nombre', ''),
            'costo': request.POST.get('costo', ''),
            'descripcion': request.POST.get('descripcion', ''),
        }
        
        ok, error = validar_datos_servicio(data)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})

        servicio = crear_servicio_db(data)

        return JsonResponse({
            'ok': True,
            'clave': servicio.clave,
            'nombre': servicio.nombre
        })
    
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})    

#.............................................................. M E D I C A M E N T O S ..............................................................................................................................-#

@login_required
def medicamentos(request):
    
    query = request.GET.get('q')

    medicamentos_list = Medicamento.objects.all()

    #  FILTRO
    if query:
        medicamentos_list = medicamentos_list.filter(
            Q(nombre__icontains=query) |
            Q(clave__icontains=query)
        )

    #  ORDEN
    medicamentos_list = medicamentos_list.order_by('nombre')

    #  PAGINACIÓN
    paginator = Paginator(medicamentos_list, 15)
    page_number = request.GET.get('page')
    medicamentos = paginator.get_page(page_number)

    contexto = {
        'seccion_activa': 'medicamentos',
        'medicamentos': medicamentos,
        'total_conteo': paginator.count,
        'query': query
    }

    return render(request, 'medicamentos/medicamentos_lista.html', contexto)


from .services import validar_datos_medicamento, crear_medicamento_db
@require_POST
def nuevo_medicamento(request):
    #recibe el post del modal y guard el medicameto
    try:
        data = {
            'nombre': request.POST.get('nombre', ''),
            'precio': request.POST.get('precio', ''),
            'descripcion': request.POST.get('descripcion', '')
        }
        
        ok, error = validar_datos_medicamento(data)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})
        
        medicamento = crear_medicamento_db(data)
        return JsonResponse({
            'ok': True, 
            'clave': medicamento.clave, 
            'nombre': medicamento.nombre,
        })
    
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})
    

#.............................................................. U S U A R I O S  ..............................................................................................................................#

@login_required
def usuarios(request):
    query = request.GET.get('q')

    usuarios_list = Usuario.objects.select_related(
        'tipo',
        'propietario',
        'recepcionista',
        'veterinario',
        'administrador',
        'estado'
    )

    # FILTRO
    if query:
        usuarios_list = usuarios_list.filter(
            Q(usuario__icontains=query) |
            Q(tipo__nombre__icontains=query)
        )

    # ORDEN
    usuarios_list = usuarios_list.order_by('usuario')

    # PAGINACIÓN
    paginator = Paginator(usuarios_list, 15)
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'usuarios/usuarios_lista.html', {
        'seccion_activa': 'usuarios',
        'usuarios': usuarios,
        'total_conteo': paginator.count,
        'query': query
    })
#............................................................... E S P E C I E S ....................................................................................................#

@login_required
def especies(request):
    
    especies_list = Especie.objects.annotate(
        total_mascotas=Count('mascota', distinct=True),
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

from .services import validar_datos_especie, crear_especie_db
@require_POST
def nueva_especie(request):
    try:
        data = {
            'nombre': request.POST.get('nombre', '')
        }
        
        ok, error = validar_datos_especie(data)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})
        
        especie = crear_especie_db(data)
        
        return JsonResponse({
            'ok': True, 
            'clave': especie.clave, 
            'nombre': especie.nombre,
        })
    
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})


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


#------------------------------------------ V E T E R I N A R I O S ------------------------------------------------------------#

@login_required
def personal(request):
    query = request.GET.get('q')
    
    veterinarios_list = Veterinario.objects.select_related(
        'especialidad'
    ).all()
    
    if query:
        veterinarios_list = veterinarios_list.filter(
            Q(nombrepila__icontains=query) |
            Q(primerapellido__icontains=query) |
            Q(segundoapellido__icontains=query) |
            Q(folio__icontains=query)
        )

    paginator = Paginator(veterinarios_list, 15)
    page_number = request.GET.get('page')
    veterinarios = paginator.get_page(page_number)

    contexto = {
        'seccion_activa': 'veterinarios',
        'veterinarios': veterinarios,
        'total_conteo': paginator.count,
        'query': query
    }

    return render(request, 'personal/personal_lista.html', contexto)
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

