#..........................................................................................................................................................

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from .models import Mascota, Propietario, Especie, Raza, Servicio, Medicamento, Usuario, Veterinario, Recepcionista, Administrador, Cita, Hospitalizacion, SignosVitales, Especialidad, Telefono, Pago, Expediente, Consulta, Receta, EdoCita, ServCons, ServHosp

from django.db.models import Value, CharField
from django.db.models.functions import Concat

from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import connection
from datetime import date, timedelta
import re
import json
#........................................................................................................................................................
# --- FUNCIONES DE VERIFICACIÓN DE ROLES ---

# En web/views.py

def es_admin(user):
    # El decorador usa esta función. Si devuelve False, te manda al login.
    if not user.is_authenticated:
        return False
    # Usamos la misma lógica que nos funcionó en el enrutador
    rol = str(getattr(user.tipo, 'codigo', user.tipo)).lower().strip()
    return rol == 'adm'

def es_veterinario(user):   
    if not user.is_authenticated: return False
    rol = str(getattr(user.tipo, 'codigo', user.tipo)).lower().strip()
    return rol == 'vet'

def es_recepcionista(user):
    if not user.is_authenticated: return False
    rol = str(getattr(user.tipo, 'codigo', user.tipo)).lower().strip()
    return rol in ['rep', 'recepcionista', 'rec']

# --- VISTAS DE CONTROL DE ACCESO ---

@login_required
def enrutador_principal(request):
    # 1. Debug: Imprime en la terminal qué está viendo Django exactamente
    tipo_obj = request.user.tipo
    # Intentamos obtener el código (ej: 'ADM') o el nombre (ej: 'Administrador')
    # Ajusta esto según los campos de tu tabla TipoUsuario
    rol_codigo = str(tipo_obj.codigo).lower().strip() if hasattr(tipo_obj, 'codigo') else str(tipo_obj).lower().strip()
    
    print(f"DEBUG: El rol detectado es: '{rol_codigo}'") # Mira esto en tu terminal

    if rol_codigo == 'adm':
        return redirect('admin_dashboard')
    elif rol_codigo == 'vet':
        return redirect('veterinario_dashboard')
    elif rol_codigo in ['rep', 'recepcionista', 'rec']: # Agregamos 'rec' por si acaso
        return redirect('recepcionista_dashboard')
    else:
        # Si entra aquí, es que 'rol_codigo' no es ninguno de los de arriba
        print("DEBUG: Rol no reconocido, cerrando sesión...")
        logout(request)
        return redirect('login')

# --- VISTAS DE DASHBOARDS (EJEMPLO) ---

@login_required
@user_passes_test(es_admin, login_url='login')
def admin_dashboard(request):
    return render(request, 'dashboard_admin.html')

@login_required
@user_passes_test(es_veterinario, login_url='login')
def veterinario_dashboard(request):
    return render(request, 'dashboard_vet.html')

@login_required
@user_passes_test(es_recepcionista, login_url='login')
def recepcionista_dashboard(request):
    return render(request, 'dashboard_rep.html')

# --- VISTA DE LOGIN Y LOGOUT ---

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            # Forzamos la asociación del backend antes del login
            if not hasattr(user, 'backend'):
                user.backend = 'web.backend.UsuarioBackend'
            
            login(request, user)
            return redirect('enrutador_principal')
        else:
            return render(request, 'login.html', {'error': 'Credenciales inválidas'})
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def inicio(request):
    """Página de inicio pública (landing page)."""
    if request.user.is_authenticated:
        return redirect('enrutador_principal')
    return render(request, 'inicio.html')
#........................................................................................................................................................


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
#------------------------------------------------------------------------------ M A S C O T A S --------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
from django.db.models import Prefetch

from django.core.cache import cache


@login_required
def mascotas(request):
    # 1. OPTIMIZACIÓN DE CACHE: Evitamos consultar Especies y Razas en cada carga.
    # Si no usas un sistema de cache (como Redis), Django usará Local Memory por defecto.
    especies = cache.get('lista_especies')
    if not especies:
        especies = list(Especie.objects.values('clave', 'nombre').order_by('nombre'))
        cache.set('lista_especies', especies, 86400) # Expira en 24h

    # 2. QUERYSET PRINCIPAL: Solo pedimos lo que la tabla muestra.
    # Usamos select_related para traer Propietario, Especie y Raza en UN SOLO viaje.
    # Usamos defer() para ignorar campos pesados que no están en la tabla.  
    mascotas_queryset = Mascota.objects.select_related(
        'propietario', 'especie', 'raza', 'estado'
    ).defer(
        'alergias', 'caracunica', 'imagen', 'sexo', 'peso', 'color', 'fechanacimiento'
    ).order_by('-folio')

    
    estado_filtro = request.GET.get('estado')
    if estado_filtro:
        mascotas_queryset = mascotas_queryset.filter(estado__clave=estado_filtro)

    # 3. PAGINACIÓN: Manejo de errores y eficiencia.
    paginator = Paginator(mascotas_queryset, 15)
    page_number = request.GET.get('page')
    
    try:
        mascotas_paginadas = paginator.get_page(page_number)
    except Exception:
        mascotas_paginadas = paginator.get_page(1)

    # 4. CONTEXTO: Limpio y eficiente.
    contexto = {
        'seccion_activa': 'mascotas',
        'mascotas': mascotas_paginadas,
        'especies': especies,
        # Si las razas son demasiadas, limitamos a 100 para no matar la latencia.
        # Lo ideal sería que este filtro fuera dinámico por AJAX.
        'razas': Raza.objects.values('clave', 'nombre').order_by('nombre')[:100],
        'total_conteo': paginator.count,
        'estado_actual': estado_filtro
    }

    return render(request, 'mascotas/mascotas_lista.html', contexto)
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@login_required
def detalles_mascota(request, folio):
    mascota = get_object_or_404(
        Mascota.objects.select_related('propietario', 'especie', 'raza','estado'), 
        folio=folio
    )
    telefonos = Telefono.objects.filter(propietario=mascota.propietario).first()
    expediente = Expediente.objects.filter(mascota=mascota).first()
    
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

    consultas = []
    hospitalizaciones = []
    recetas = []
    
    if expediente:
        consultas = Consulta.objects.filter(
            expediente=expediente
        ).select_related('cita__veterinario', 'cita__estado').order_by('-cita__fecha')
        
        hospitalizaciones = Hospitalizacion.objects.filter(
            expediente=expediente
        ).select_related('veterinario', 'estado').order_by('-fechaingreso')
        
        recetas_qs = Receta.objects.filter(
            consulta__expediente=expediente
        ).select_related('consulta__cita').order_by('-fecha')
        
        receta_hosp_qs = Receta.objects.filter(
            hospitalizacion__expediente=expediente
        ).select_related('hospitalizacion').order_by('-fecha')
        
        #todas las recetas + tratamientos
        todas_recetas = list(recetas_qs) + list(receta_hosp_qs)
        todas_recetas.sort(key=lambda r: r.fecha, reverse=True)

        with connection.cursor() as cursor:
            for receta in todas_recetas:
                cursor.execute("""
                    SELECT m.nombre, m.clave, t.dosis, t.frecuencia,
                           t.duracion, t.notas, t.cantidad, t.estado
                    FROM tratamiento t
                    JOIN medicamento m ON t.medicamento = m.clave
                    WHERE t.receta = %s
                """, [receta.numero])
                cols = [c[0] for c in cursor.description]
                receta.tratamientos = [dict(zip(cols, row)) for row in cursor.fetchall()]
                receta.origen = 'Consulta' if receta.consulta_id else 'Hospitalización'
            recetas = todas_recetas
    
    historial = []
    for c in consultas:
        historial.append({'tipo': 'consulta', 'fecha': c.cita.fecha, 'obj': c})
    for h in hospitalizaciones:
        historial.append({'tipo': 'hospitalizacion', 'fecha': h.fechaingreso, 'obj': h})
    historial.sort(key=lambda x: x['fecha'], reverse=True)
    
    num_consultas = len([e for e in historial if e['tipo'] == 'consulta'])
    num_hosp = len([e for e in historial if e['tipo'] == 'hospitalizacion'])
    
    # Última cita próxima pendiente
    proxima_cita = Cita.objects.filter(
        mascota=mascota,
        estado__nombre='Pendiente',
        fecha__gte=hoy
    ).order_by('fecha', 'hora').first()

    contexto = {
        'seccion_activa':   'mascotas',
        'mascota':           mascota,
        'expediente':        expediente,
        'telefonos':         telefonos,
        'historial':         historial,
        'num_consultas':     num_consultas,
        'num_hosp':          num_hosp,
        'recetas':           recetas,
        'proxima_cita':      proxima_cita,
    }

    return render(request, 'mascotas/mascotas_detalles.html', contexto)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
from .services import validar_datos_mascota, crear_mascota_db, generar_folio_mascota

def crear_mascota(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    try:
        # Hacemos una copia para poder manipular los datos si es necesario
        data = request.POST.copy()

        with transaction.atomic():
            # 1. VALIDACIÓN
            # Asegúrate de que esta función devuelva (True, None) o (False, "Error")
            valido, error = validar_datos_mascota(data)
            if not valido:
                return JsonResponse({'ok': False, 'error': error})

            # 2. CREACIÓN EN DB
            # Esta función debe usar Especie.objects.get(clave=...) y Raza.objects.get(clave=...)
            mascota = crear_mascota_db(data)

        # RESPUESTA DE ÉXITO
        return JsonResponse({
            'ok': True,
            'message': 'Mascota guardada correctamente', # <--- Esta clave lee el JS
            'id': mascota.folio
        })

    except IntegrityError as e:
        print(f"ERROR DE INTEGRIDAD: {e}") # Mira esto en tu terminal de VS Code
        return JsonResponse({
            'ok': False,
            'error': f'Error de base de datos: {str(e)}' # Esto te dirá el campo exacto
        })

    except ValueError as e:
        # Captura errores de conversión (ej: float() de un peso inválido o formato de fecha)
        return JsonResponse({
            'ok': False,
            'error': f'Error en el formato de los datos: {str(e)}'
        })

    except Exception as e:
        # Captura cualquier otro error inesperado
        return JsonResponse({
            'ok': False,
            'error': f'Ocurrió un error inesperado: {str(e)}'
        })


def obtener_folio_mascota(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False}, status=405)

    return JsonResponse({'folio': generar_folio_mascota()})


#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def buscar_propietario(request):
    folio = request.GET.get('folio')

    try:
        propietario = Propietario.objects.get(folio=folio)

        nombre_completo = f"{propietario.nombrepila} {propietario.primerapellido} {propietario.segundoapellido or ''}".strip()

        return JsonResponse({
            'ok': True,
            'folio': propietario.folio,
            'nombre': nombre_completo
        })

    except Propietario.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Propietario no encontrado'
        })
        
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def obtener_razas(request):
    especie_id = request.GET.get('especie_id')
    
    # Filtramos las razas por el ID/Clave de la especie
    # Usamos 'especie' porque ese es el nombre del campo ForeignKey en tu modelo Raza
    razas = Raza.objects.filter(especie=especie_id).order_by('nombre')
    
    # IMPORTANTE: Vamos a imprimir en la terminal para estar 100% seguros
    print(f"Buscando razas para especie: {especie_id}")
    
    # Enviamos 'clave' (que es tu PK) y 'nombre'
    data = list(razas.values('clave', 'nombre'))
    
    print(f"Datos enviados al JS: {data}") # <--- Mira esto en tu terminal de VS Code/PyCharm
    
    return JsonResponse(data, safe=False)
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
    propietario = get_object_or_404(Propietario, folio=folio)
    telefonos   = Telefono.objects.filter(propietario=propietario).first()
    mascotas    = Mascota.objects.select_related('especie', 'raza', 'estado').filter(propietario=propietario)
    hoy         = timezone.now().date()
    
    for m in mascotas:
        anios = hoy.year - m.fechanacimiento.year
        meses = hoy.month - m.fechanacimiento.month
        
        # Ajusta si aun no a pasado el dia de su cumpleaños este mes/año
        if hoy.day < m.fechanacimiento.day:
            anios -= 1
            
        if meses < 0:
            anios -= 1
            meses += 12
            
        if anios == 0:
            m.edad_formateada = f"{meses} mes{'es' if meses != 1 else ''}"
        else:
            m.edad_formateada = f"{anios} año{'s' if anios != 1 else ''}"
    
    # Consultas de todas las mascotas del propietario
    consultas = Consulta.objects.select_related(
        'cita__mascota', 'cita__veterinario'
    ).filter(
        cita__propietario=propietario
    ).order_by('-cita__fecha')[:10]
    
    # Hospitalizaciones de todas las mascotas del propietario
    hospitalizaciones = Hospitalizacion.objects.select_related(
        'expediente__mascota', 'veterinario', 'estado'
    ).filter(
        expediente__mascota__propietario=propietario
    ).order_by('-fechaingreso')[:10]
    
    # Mezclar y ordenar las últimas visitas por fecha descendente
    visitas = []
    for c in consultas:
        visitas.append({
            'tipo':        'consulta',
            'fecha':        c.cita.fecha,
            'mascota':      c.cita.mascota.nombre,
            'motivo':       c.cita.motivo,
            'veterinario':  f"{c.cita.veterinario.nombrepila} {c.cita.veterinario.primerapellido}",
            'estado':       c.cita.estado.nombre,
            'url':          f"/consultas/{c.numero}/ver/",
        })
    
    for h in hospitalizaciones:
        visitas.append({
            'tipo':        'hospitalizacion',
            'fecha':        h.fechaingreso,
            'mascota':      h.expediente.mascota.nombre,
            'motivo':       h.diagnoingreso,
            'veterinario':  f"{h.veterinario.nombrepila} {h.veterinario.primerapellido}",
            'estado':       h.estado.nombre,
            'url':          f"/hospitalizacion/{h.numero}/ver/",
        })
        
    visitas.sort(key=lambda v: v['fecha'], reverse=True)
    visitas = visitas[:8]  # máximo 8 en el perfil
      
    contexto = {
        'seccion_activa': 'propietarios',
        'propietario': propietario,
        'telefonos': telefonos,
        'mascotas': mascotas,
        'mascotas_count': mascotas.count(),
        'especies': Especie.objects.order_by('nombre'),
        'visitas': visitas,
    }

    return render(request, 'propietarios/propietarios_detalles.html', contexto)

@require_POST
def editar_propietario(request, folio):
    from .services import validar_datos, formatear_telefono
    propietario = get_object_or_404(Propietario, folio=folio)

    data = request.POST.copy()
    valido, error = validar_datos(data)
    if not valido:
        return JsonResponse({'ok': False, 'error': error})

    try:
        from .services import formatear_texto, limpiar_espacios
        propietario.nombrepila      = data.get('nombre', '').strip().title()
        propietario.primerapellido  = data.get('apellido_paterno', '').strip().title()
        propietario.segundoapellido = data.get('apellido_materno', '').strip().title() or None
        propietario.correo          = data.get('correo', '').strip().lower()
        propietario.dircalle        = data.get('calle', '').strip().title()
        propietario.dirnum          = data.get('numero', '').strip()
        propietario.dircolonia      = data.get('colonia', '').strip().title()
        propietario.save()

        # Actualizar teléfono
        tel = Telefono.objects.filter(propietario=propietario).first()
        if tel:
            from .services import formatear_telefono, limpiar_espacios
            tel.numprincipal  = formatear_telefono(limpiar_espacios(data.get('tel_principal')))
            tel.numsecundario = formatear_telefono(limpiar_espacios(data.get('tel_secundario'))) if data.get('tel_secundario') else None
            tel.save()

        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})
      
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
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')

    citas_list = Cita.objects.select_related(
        'mascota__raza__especie',
        'propietario',
        'veterinario',
        'estado'
    ).order_by('-fecha', '-hora')

    if query:
        citas_list = citas_list.filter(
            Q(folio__icontains=query) |
            Q(mascota__nombre__icontains=query) |
            Q(veterinario__nombrepila__icontains=query) |
            Q(propietario__primerapellido__icontains=query)
        )

    if estado:
        citas_list = citas_list.filter(estado__nombre=estado)
    
    # Stats
    conteos = Cita.objects.values('estado__nombre').annotate(total=Count('folio'))
    stats = {item['estado__nombre']: item['total'] for item in conteos}

    # Paginación
    paginator = Paginator(citas_list, 15)
    page_number = request.GET.get('page')
    citas = paginator.get_page(page_number)

    # Datos para los selects del modal — listas independientes
    propietarios = Propietario.objects.order_by('primerapellido', 'nombrepila')
    veterinarios = Veterinario.objects.order_by('primerapellido', 'nombrepila')
    estados_cita = EdoCita.objects.all()
    
    # Mascotas en JSON para el filtro dinámico por propietario
    mascotas_json = list(
        Mascota.objects.select_related('propietario').values(
            'folio', 'nombre', 'propietario__folio'
        )
    )
    
    contexto = {
        'seccion_activa': 'citas',
        'citas': citas,
        'stats': stats,
        'total_conteo': paginator.count,
        'query': query,
        'propietarios': propietarios,
        'veterinarios': veterinarios,
        'estados_cita': estados_cita,
        'mascotas_json': mascotas_json,
    }

    return render(request, 'citas/citas_lista.html', contexto)

@require_POST
def nueva_cita(request):
    from .services import validar_datos_cita, crear_cita_db
    try:
        data = {
            'propietario': request.POST.get('propietario', ''),
            'mascota':     request.POST.get('mascota', ''),
            'veterinario': request.POST.get('veterinario', ''),
            'fecha':       request.POST.get('fecha', ''),
            'hora':        request.POST.get('hora', ''),
            'motivo':      request.POST.get('motivo', ''),
        }
 
        ok, error = validar_datos_cita(data)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})
 
        cita = crear_cita_db(data)
 
        return JsonResponse({
            'ok':    True,
            'folio': cita.folio,
            'fecha': str(cita.fecha),
        })
 
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})
    
@require_POST
def editar_cita(request, folio):
    from .services import validar_datos_editar_cita
    try:
        cita = get_object_or_404(Cita, folio=folio)
        data = {
            'fecha':       request.POST.get('fecha', ''),
            'hora':        request.POST.get('hora', ''),
            'veterinario': request.POST.get('veterinario', ''),
            'estado':      request.POST.get('estado', ''),
            'motivo':      request.POST.get('motivo', ''),
        }

        ok, error = validar_datos_editar_cita(data, folio_actual=folio)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})

        cita.fecha    = data['fecha']
        cita.hora     = data['hora']
        cita.motivo   = data['motivo'].strip()
        cita.veterinario = Veterinario.objects.get(folio=data['veterinario'])
        cita.estado      = EdoCita.objects.get(clave=data['estado'])
        cita.save()

        return JsonResponse({'ok': True, 'folio': cita.folio})

    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})

#------------------------------------------------------------------ C O N S U L T A S ------------------------------------------------------------#

@login_required
def consultas(request):
    query = request.GET.get('q', '').strip()
    
    consultas_list = Consulta.objects.select_related(
        'cita__mascota__raza__especie',
        'cita__mascota__propietario',
        'cita__veterinario',
    ).order_by('-numero')
    
    if query:
        consultas_list = consultas_list.filter(
            Q(cita__mascota__nombre__icontains=query) |
            Q(cita__propietario__primerapellido__icontains=query) |
            Q(diagnostico__icontains=query)
        )
    
    # Paginación
    paginator = Paginator(consultas_list, 15)
    page_number = request.GET.get('page')
    consultas = paginator.get_page(page_number)
    
    #Citas pendientes para el selec del modal :)
    citas_pendientes = Cita.objects.select_related(
        'mascota',
        'propietario',
        'veterinario',
        'estado',
    ).filter(
        estado__nombre='Pendiente'
    ).order_by('fecha', 'hora')
    
    contexto = {
        'seccion_activa': 'consultas',
        'consultas': consultas,
        'total_conteo': paginator.count,
        'query': query,
        'citas_pendientes': citas_pendientes,
    }
    
    return render(request, 'consultas/consultas_lista.html', contexto)

@login_required
def iniciar_consulta(request, folio_cita):
    """
    GET  → muestra el formulario de nueva consulta para la cita indicada.
    POST → guarda la consulta y redirige a la lista.
    """
    from .services import validar_datos_consulta, guardar_consulta_db
 
    cita = get_object_or_404(
        Cita.objects.select_related(
            'mascota__raza__especie', 'mascota__propietario',
            'veterinario', 'estado'
        ),
        folio=folio_cita
    )
    
    mascota = cita.mascota
    
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
    
 
    # Consultas previas de esta mascota (historial)
    expediente = Expediente.objects.filter(mascota=cita.mascota).first()
    consultas_previas = []
    if expediente:
        consultas_previas = Consulta.objects.filter(
            expediente=expediente
        ).select_related('cita__veterinario').exclude(
            cita=cita
        ).order_by('-cita__fecha')[:5]
 
    medicamentos_disponibles = Medicamento.objects.order_by('nombre')
 
    if request.method == 'POST':
        from .services import validar_datos_consulta, guardar_consulta_db
        
        if Consulta.objects.filter(cita=cita).exists():
            return redirect(f'/consultas/{Consulta.objects.get(cita=cita).numero}/ver/') 
        
        data = {
            'sintomas':          request.POST.get('sintomas', ''),
            'diagnostico':       request.POST.get('diagnostico', ''),
            'observaciones':     request.POST.get('observaciones', ''),
            'temperatura':       request.POST.get('temperatura', ''),
            'peso':              request.POST.get('peso', 0),
            'freccardiaca':      request.POST.get('freccardiaca', ''),
            'frecrespiratoria':  request.POST.get('frecrespiratoria', ''),
            'instrugenerales':   request.POST.get('instrugenerales', ''),
            'medicamentos_json': request.POST.get('medicamentos_json', '[]'),
            'servicios_json':    request.POST.get('servicios_json', '[]'),
        }
        ok, error = validar_datos_consulta(data)
        if not ok:
            return render(request, 'consultas/consultas_inicio.html', {
                'seccion_activa': 'consultas',
                'cita': cita,
                'modo': 'iniciar',
                'error': error,
                'consultas_previas': consultas_previas,
                'medicamentos_disponibles': medicamentos_disponibles,
                'data': data,
                'servicios_disponibles': Servicio.objects.order_by('nombre'),
                'edad': mascota.edad
            })
 
        consulta = guardar_consulta_db(cita, data)
        from .services import guardar_servicios_consulta
        return redirect(f'/consultas/{consulta.numero}/ver/?guardado=1')
 
    return render(request, 'consultas/consultas_inicio.html', {
        'seccion_activa': 'consultas',
        'cita': cita,
        'modo': 'iniciar',
        'consultas_previas': consultas_previas,
        'medicamentos_disponibles': medicamentos_disponibles,
        'servicios_disponibles': Servicio.objects.order_by('nombre'),
        'edad': mascota.edad
    })
    
@login_required
def ver_consulta(request, numero):
    """Vista de solo lectura de una consulta."""
    
    from .services import obtener_servicios_consulta
    
    consulta = get_object_or_404(
        Consulta.objects.select_related(
            'cita__mascota__raza__especie',
            'cita__mascota__propietario',
            'cita__veterinario',
            'expediente',
        ),
        numero=numero
    )
    
    mascota = consulta.cita.mascota
    
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
    
    receta = Receta.objects.filter(consulta=consulta).first()
    tratamientos = []

    if receta:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT m.nombre, m.clave, t.dosis, t.frecuencia, 
                    t.duracion, t.notas, t.cantidad
                FROM tratamiento t
                JOIN medicamento m ON t.medicamento = m.clave
                WHERE t.receta = %s
            """, [receta.numero])
            cols = [col[0] for col in cursor.description]
            tratamientos = [dict(zip(cols, row)) for row in cursor.fetchall()]
 
    expediente = consulta.expediente
    consultas_previas = Consulta.objects.filter(
        expediente=expediente
    ).select_related('cita__veterinario').exclude(
        numero=numero
    ).order_by('-cita__fecha')[:5]
 
    guardado = request.GET.get('guardado') == '1'
 
    return render(request, 'consultas/consultas_inicio.html', {
        'seccion_activa':   'consultas',
        'cita':             consulta.cita,
        'consulta':         consulta,
        'receta':           receta,
        'tratamientos':     tratamientos,
        'modo':             'ver',
        'consultas_previas': consultas_previas,
        'guardado':         guardado,
        'servicios_consulta': obtener_servicios_consulta(consulta.numero),
        'edad':             mascota.edad
    })
 
 
@login_required
def editar_consulta(request, numero):
    """Editar síntomas, diagnóstico y observaciones de una consulta."""
    from .services import actualizar_consulta_db
 
    consulta = get_object_or_404(
        Consulta.objects.select_related(
            'cita__mascota__raza__especie',
            'cita__mascota__propietario',
            'cita__veterinario',
        ),
        numero=numero
    )
    
    mascota = consulta.cita.mascota
    
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
    
    # obtener receta y tratamiento
    receta = Receta.objects.filter(consulta=consulta).first()
    tratamientos = []
    if receta:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT m.nombre, m.clave, t.dosis, t.frecuencia, 
                    t.duracion, t.notas, t.cantidad
                FROM tratamiento t
                JOIN medicamento m ON t.medicamento = m.clave
                WHERE t.receta = %s
            """, [receta.numero])
            cols = [col[0] for col in cursor.description]
            tratamientos = [dict(zip(cols, row)) for row in cursor.fetchall()]
    # ------------------------------------------------------------------
    
    expediente = consulta.expediente
    consultas_previas = Consulta.objects.filter(
        expediente=expediente
    ).select_related('cita__veterinario').exclude(
        numero=numero
    ).order_by('-cita__fecha')[:5]

    if request.method == 'POST':
        data = {
            'sintomas':      request.POST.get('sintomas', ''),
            'diagnostico':   request.POST.get('diagnostico', ''),
            'observaciones': request.POST.get('observaciones', ''),
        }
        if not data['sintomas'] or not data['diagnostico'] or not data['observaciones']:
            return render(request, 'consultas/consultas_inicio.html', {
                'seccion_activa': 'consultas',
                'cita': consulta.cita,
                'consulta': consulta,
                'modo': 'editar',
                'error': 'Todos los campos de texto son obligatorios',
                'consultas_previas': consultas_previas,
                'receta': receta,
                'tratamientos': tratamientos
            })
 
        consulta = actualizar_consulta_db(consulta, data)
        return redirect(f'/consultas/{consulta.numero}/ver/?guardado=1')
 
    return render(request, 'consultas/consultas_inicio.html', {
        'seccion_activa': 'consultas',
        'cita':           consulta.cita,
        'consulta':       consulta,
        'modo':           'editar',
        'consultas_previas': consultas_previas,
        'receta':           receta,
        'tratamientos':     tratamientos,
        'edad':             mascota.edad,
    })

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

#.................................................................... H O S P I T A L I Z A C I O N E S ...................................................................#
@login_required
def hospitalizacion(request):
    hoy = timezone.now().date()
 
    # Activas primero, luego dadas de alta, ordenadas por fecha
    hosp_list = Hospitalizacion.objects.select_related(
        'veterinario', 'estado',
        'expediente__mascota__raza__especie',
        'expediente__mascota__propietario',
    ).order_by('-fechaalta', '-fechaingreso')
    # fechaalta NULL → son las activas, van primero (NULL < valor en ORDER BY ASC)
 
    activas = hosp_list.filter(fechaalta__isnull=True)
    revisiones_hoy = SignosVitales.objects.filter(fecha=hoy).values_list('hospitalizacion_id', flat=True)
    pendientes  = activas.exclude(numero__in=revisiones_hoy).count()
    altas_hoy   = hosp_list.filter(fechaalta=hoy).count()
 
    # Consultas con estado 'Atendida' para el select de iniciar hospitalización
    consultas_atendidas = Consulta.objects.select_related(
        'cita__mascota', 'cita__propietario', 'cita__veterinario'
    ).filter(
        cita__estado__nombre='Atendida'
    ).exclude(
        # Excluir consultas que ya tienen hospitalización activa
        hospitalizacion__isnull=False
    ).order_by('-cita__fecha')
    
    contexto = {
        'seccion_activa':      'hospitalizacion',
        'hospitalizaciones':   hosp_list,
        'activas':             activas.count(),
        'admitidas_hoy':       activas.filter(fechaingreso=hoy).count(),
        'pendientes':          pendientes,
        'altas_hoy':           altas_hoy,
        'total_conteo':        hosp_list.count(),
        'consultas_atendidas': consultas_atendidas,
    }
    return render(request, 'hospitalizacion/hospitalizacion_lista.html', contexto)

@login_required
def iniciar_hospitalizacion(request, consulta_numero):
    """
    GET  → formulario de nueva hospitalización.
    POST → guarda y redirige a ver_hospitalizacion.
    """
    from .services import validar_datos_hospitalizacion, crear_hospitalizacion_db
 
    consulta = get_object_or_404(
        Consulta.objects.select_related(
            'cita__mascota__raza__especie',
            'cita__mascota__propietario',
            'cita__veterinario',
            'expediente',
        ),
        numero=consulta_numero
    )
    
    mascota = consulta.cita.mascota
    
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
    
    veterinarios         = Veterinario.objects.order_by('primerapellido')
    medicamentos_disp    = Medicamento.objects.order_by('nombre')
    servicios_disp       = Servicio.objects.order_by('nombre')
 
    if request.method == 'POST':
        data = {
            'diagnoingreso':    request.POST.get('diagnoingreso', ''),
            'obsergenerales':   request.POST.get('obsergenerales', ''),
            'veterinario':      request.POST.get('veterinario', ''),
            'temperatura':      request.POST.get('temperatura', ''),
            'freccardiaca':     request.POST.get('freccardiaca', ''),
            'frecrespiratoria': request.POST.get('frecrespiratoria', ''),
            'instrugenerales':  request.POST.get('instrugenerales', ''),
            'medicamentos_json': request.POST.get('medicamentos_json', '[]'),
            'servicios_json':   request.POST.get('servicios_json', '[]'),
        }
 
        ok, error = validar_datos_hospitalizacion(data)
        if not ok:
            return render(request, 'hospitalizacion/hospitalizacion_inicio.html', {
                'seccion_activa': 'hospitalizacion',
                'consulta': consulta,
                'error': error,
                'veterinarios': veterinarios,
                'medicamentos_disponibles': medicamentos_disp,
                'servicios_disponibles': servicios_disp,
                'edad': mascota.edad,
            })
 
        hosp = crear_hospitalizacion_db(consulta, data)
        return redirect(f'/hospitalizacion/{hosp.numero}/ver/?guardado=1')
 
    return render(request, 'hospitalizacion/hospitalizacion_inicio.html', {
        'seccion_activa':          'hospitalizacion',
        'consulta':                consulta,
        'veterinarios':            veterinarios,
        'medicamentos_disponibles': medicamentos_disp,
        'servicios_disponibles':   servicios_disp,
        'edad':                    mascota.edad,
    })
    
@login_required
def ver_hospitalizacion(request, numero):
    hosp = get_object_or_404(
        Hospitalizacion.objects.select_related(
            'veterinario', 'estado',
            'expediente__mascota__raza__especie',
            'expediente__mascota__propietario',
            'consulta__cita',
        ),
        numero=numero
    )
    
    mascota = hosp.consulta.cita.mascota
    
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
 
    from .services import obtener_servicios_hosp, obtener_signos_vitales
 
    # Receta y tratamientos (SQL directo)
    receta = Receta.objects.filter(hospitalizacion=hosp).first()
    tratamientos = []
    if receta:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT m.nombre, m.clave, t.dosis, t.frecuencia,
                       t.duracion, t.notas, t.cantidad
                FROM tratamiento t
                JOIN medicamento m ON t.medicamento = m.clave
                WHERE t.receta = %s
            """, [receta.numero])
            cols = [col[0] for col in cursor.description]
            tratamientos = [dict(zip(cols, row)) for row in cursor.fetchall()]
 
    servicios     = obtener_servicios_hosp(hosp.numero)
    signos_vitales = obtener_signos_vitales(hosp.numero)
    guardado      = request.GET.get('guardado') == '1'
 
    return render(request, 'hospitalizacion/hospitalizacion_inicio.html', {
        'seccion_activa':  'hospitalizacion',
        'consulta':        hosp.consulta,
        'hosp':            hosp,
        'modo':            'ver',
        'tratamientos':    tratamientos,
        'servicios':       servicios,
        'signos_vitales':  signos_vitales,
        'guardado':        guardado,
        'edad':            mascota.edad,
    })

@login_required
def editar_hospitalizacion(request, numero):
    from .services import actualizar_hospitalizacion_db, obtener_servicios_hosp, obtener_signos_vitales
    
    hosp = get_object_or_404(
        Hospitalizacion.objects.select_related(
            'veterinario', 'estado',
            'expediente__mascota__raza__especie',
            'expediente__mascota__propietario',
            'consulta__cita',
        ),
        numero=numero
    )
    
    mascota = hosp.consulta.cita.mascota
    
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
    
    medicamentos_disp = Medicamento.objects.order_by('nombre')
    servicios_disp    = Servicio.objects.order_by('nombre')
    
    # Receta y tratamientos actuales (para mostrar en la sidebar)
    receta = Receta.objects.filter(hospitalizacion=hosp).first()
    tratamientos = []
    if receta:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT m.nombre, m.clave, t.dosis, t.frecuencia,
                       t.duracion, t.notas, t.cantidad
                FROM tratamiento t
                JOIN medicamento m ON t.medicamento = m.clave
                WHERE t.receta = %s
            """, [receta.numero])
            cols = [col[0] for col in cursor.description]
            tratamientos = [dict(zip(cols, row)) for row in cursor.fetchall()]
    
    servicios_actuales = obtener_servicios_hosp(hosp.numero)
    signos_vitales     = obtener_signos_vitales(hosp.numero)    
    
    if request.method == 'POST':
        data = {
            'diagnoingreso':    request.POST.get('diagnoingreso', ''),
            'obsergenerales':   request.POST.get('obsergenerales', ''),
            'temperatura':      request.POST.get('temperatura', ''),
            'freccardiaca':     request.POST.get('freccardiaca', ''),
            'frecrespiratoria': request.POST.get('frecrespiratoria', ''),
            'peso':             request.POST.get('peso', ''),
            'instrugenerales':  request.POST.get('instrugenerales', ''),
            'medicamentos_json': request.POST.get('medicamentos_json', '[]'),
            'servicios_json':   request.POST.get('servicios_json', '[]'),
        }
        
        actualizar_hospitalizacion_db(hosp, data)
        return redirect(f'/hospitalizacion/{hosp.numero}/ver/?guardado=1')
 
    return render(request, 'hospitalizacion/hospitalizacion_inicio.html', {
        'seccion_activa':          'hospitalizacion',
        'consulta':                hosp.consulta,
        'hosp':                    hosp,
        'modo':                    'editar',
        'tratamientos':            tratamientos,
        'servicios':               servicios_actuales,
        'signos_vitales':          signos_vitales,
        'medicamentos_disponibles': medicamentos_disp,
        'servicios_disponibles':   servicios_disp,
    })

@require_POST
def dar_alta_hospitalizacion(request, numero):
    from .services import dar_de_alta_hospitalizacion
    try:
        hosp = get_object_or_404(Hospitalizacion, numero=numero)
        if hosp.fechaalta:
            return JsonResponse({'ok': False, 'error': 'Esta hospitalización ya fue dada de alta'})
        dar_de_alta_hospitalizacion(hosp, {})
        return JsonResponse({'ok': True, 'numero': hosp.numero})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})

#............................................................................. P A G O S ..................................................................................#
@login_required
def pagos(request):
    
    pagos_list = Pago.objects.select_related(
        'consulta__cita__mascota__propietario',
        'consulta__cita__estado',
        'hospitalizacion__estado',
    ).order_by('-fecha', '-hora')
    
    # Consultas atendidas sin pago aún
    consultas_sin_pago = Consulta.objects.select_related(
        'cita__mascota__propietario', 'cita__estado'
    ).filter(
        cita__estado__nombre='Atendida'
    ).exclude(
        pago__isnull=False   # ya tienen pago
    ).order_by('-cita__fecha')
    
    # Hospitalizaciones con alta sin pago aún
    hosps_sin_pago = Hospitalizacion.objects.select_related(
        'expediente__mascota__propietario', 'estado', 'consulta'
    ).filter(
        fechaalta__isnull=False,
        estado__nombre__icontains='Alta',
    ).exclude(
        pago__isnull=False
    ).order_by('-fechaalta')
    
    contexto = {
        'seccion_activa':     'pagos',
        'pagos':              pagos_list,
        'consultas_sin_pago': consultas_sin_pago,
        'hosps_sin_pago':     hosps_sin_pago,
    }
    return render(request, 'pagos/pagos_lista.html', contexto)

@login_required
def ver_recibo(request, codigo):
    """Vista de solo lectura del recibo de un pago."""
    from .services import obtener_desglose_consulta, obtener_desglose_hospitalizacion
 
    pago = get_object_or_404(
        Pago.objects.select_related(
            'consulta__cita__mascota__raza__especie',
            'consulta__cita__mascota__propietario',
            'consulta__cita__veterinario',
            'hospitalizacion',
        ),
        codigo=codigo
    )
 
    mascota     = pago.consulta.cita.mascota
    propietario = pago.consulta.cita.propietario
    veterinario = pago.consulta.cita.veterinario
 
    if pago.hospitalizacion:
        items, total, dias = obtener_desglose_hospitalizacion(pago.hospitalizacion.numero)
        tipo = 'hospitalizacion'
    else:
        items, total = obtener_desglose_consulta(pago.consulta.numero)
        tipo  = 'consulta'
        dias  = None
 
    return render(request, 'pagos/pagos_recibo.html', {
        'seccion_activa': 'pagos',
        'pago':           pago,
        'mascota':        mascota,
        'propietario':    propietario,
        'veterinario':    veterinario,
        'items':          items,
        'total':          total,
        'tipo':           tipo,
        'dias':           dias,
    })
    
@login_required
def previsualizar_pago(request):
    """
    GET con ?tipo=consulta&id=N o ?tipo=hospitalizacion&id=N
    Devuelve JSON con el desglose para mostrar en el modal antes de confirmar.
    """
    from .services import obtener_desglose_consulta, obtener_desglose_hospitalizacion
 
    tipo = request.GET.get('tipo')
    id_  = request.GET.get('id')
 
    if not tipo or not id_:
        return JsonResponse({'ok': False, 'error': 'Parámetros incompletos'})
 
    try:
        if tipo == 'consulta':
            items, total = obtener_desglose_consulta(int(id_))
            dias = None
        elif tipo == 'hospitalizacion':
            items, total, dias = obtener_desglose_hospitalizacion(int(id_))
        else:
            return JsonResponse({'ok': False, 'error': 'Tipo inválido'})
 
        return JsonResponse({
            'ok':    True,
            'items': [
                {
                    'nombre':      i.get('nombre', ''),
                    'descripcion': i.get('descripcion', '') or i.get('nota', ''),
                    'costo':       float(i.get('costo', 0)),
                    'cantidad':    int(i.get('cantidad', 1)),
                    'subtotal':    float(i.get('subtotal', 0)),
                    'tipo':        i.get('tipo', ''),
                }
                for i in items
            ],
            'total': float(total),
            'dias':  dias,
        })
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})
    
@require_POST
def confirmar_pago(request):
    """Crea el registro de pago después de confirmar en el modal."""
    from .services import crear_pago_db, obtener_desglose_consulta, obtener_desglose_hospitalizacion
 
    tipo = request.POST.get('tipo')
    id_  = request.POST.get('id')
 
    if not tipo or not id_:
        return JsonResponse({'ok': False, 'error': 'Datos incompletos'})
 
    try:
        id_ = int(id_)
        if tipo == 'consulta':
            _, total = obtener_desglose_consulta(id_)
        elif tipo == 'hospitalizacion':
            _, total, _ = obtener_desglose_hospitalizacion(id_)
        else:
            return JsonResponse({'ok': False, 'error': 'Tipo inválido'})
 
        pago = crear_pago_db(tipo, id_, total)
        return JsonResponse({'ok': True, 'codigo': pago.codigo})
 
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})

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

from .services import validar_datos_raza, crear_raza_db
@require_POST
def nueva_raza(request):
    try:
        data = {
            'especie': request.POST.get('especie', ''),
            'nombre': request.POST.get('nombre', ''),
        }
        
        ok, error = validar_datos_raza(data)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})
        
        raza = crear_raza_db(data)
        
        return JsonResponse({
            'ok': True, 
            'clave': raza.clave, 
            'nombre': raza.nombre,
        })
    
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})
    
#------------------------------------------ V E T E R I N A R I O S ------------------------------------------------------------#

@login_required
def personal(request):
    query = request.GET.get('q', '')
    
    veterinarios_list = Veterinario.objects.select_related('especialidad').all()
    
    if query:
        veterinarios_list = veterinarios_list.filter(
            Q(nombrepila__icontains=query) |
            Q(primerapellido__icontains=query) |
            Q(segundoapellido__icontains=query) |
            Q(folio__icontains=query)
        )

    veterinarios_list = veterinarios_list.order_by('primerapellido', 'nombrepila')
    paginator = Paginator(veterinarios_list, 15)
    page_number = request.GET.get('page')
    veterinarios = paginator.get_page(page_number)

    especialidades = Especialidad.objects.order_by('nombre')

    #Citas de la semana actuaal
    hoy        = date.today()
    inicio_sem = hoy - timedelta(days=hoy.weekday())   # lunes
    fin_sem    = inicio_sem + timedelta(days=6)          # domingo
    
    citas_semana = Cita.objects.select_related(
        'mascota', 'propietario', 'veterinario', 'estado'
    ).filter(
        fecha__range=(inicio_sem, fin_sem)
    ).order_by('fecha', 'hora')
    
    # Serializar citas para la agenda en JS
    citas_json = []
    for c in citas_semana:
        dia = (c.fecha - inicio_sem).days   # 0=lun … 6=dom
        hora_h = c.hora.hour - 8            # índice en HORAS (08:00 = 0)
        if 0 <= hora_h <= 8:
            citas_json.append({
                'dia':         dia,
                'hora':        hora_h,
                'titulo':      f"{c.mascota.nombre}",
                'sub':         f"{c.motivo} • {c.propietario.nombrepila} {c.propietario.primerapellido}",
                'tiempo':      f"{c.hora.strftime('%H:%M')}",
                'estado':      c.estado.nombre,
                'veterinario': c.veterinario.folio,
            })
    
    contexto = {
        'seccion_activa': 'veterinarios',
        'veterinarios': veterinarios,
        'total_conteo': paginator.count,
        'total_especialidades': especialidades.count(),
        'especialidades': especialidades,
        'query': query,
        'inicio': inicio_sem.isoformat(),
        'citas_json': citas_json,
    }

    return render(request, 'personal/personal_lista.html', contexto)

@require_POST
def nuevo_veterinario(request):
    from .services import validar_datos_veterinario, crear_veterinario_db
    try:
        data = {
            'nombre':           request.POST.get('nombre', ''),
            'apellido_paterno': request.POST.get('apellido_paterno', ''),
            'apellido_materno': request.POST.get('apellido_materno', ''),
            'correo':           request.POST.get('correo', ''),
            'telefono':         request.POST.get('telefono', ''),
            'cedula':           request.POST.get('cedula', ''),
            'especialidad':     request.POST.get('especialidad', ''),
        }
 
        ok, error = validar_datos_veterinario(data)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})
 
        vet = crear_veterinario_db(data)
        return JsonResponse({
            'ok':     True,
            'folio':  vet.folio,
            'nombre': f"{vet.nombrepila} {vet.primerapellido}",
        })
 
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})
    
@require_POST
def editar_veterinario(request, folio):
    from .services import validar_datos_veterinario, editar_veterinario_db
    try:
        vet = get_object_or_404(Veterinario, folio=folio)
        data = {
            'nombre':           request.POST.get('nombre', ''),
            'apellido_paterno': request.POST.get('apellido_paterno', ''),
            'apellido_materno': request.POST.get('apellido_materno', ''),
            'correo':           request.POST.get('correo', ''),
            'telefono':         request.POST.get('telefono', ''),
            'especialidad':     request.POST.get('especialidad', ''),
        }
 
        ok, error = validar_datos_veterinario(data, folio_actual=folio)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})
 
        vet = editar_veterinario_db(vet, data)
        return JsonResponse({
            'ok':     True,
            'folio':  vet.folio,
            'nombre': f"{vet.nombrepila} {vet.primerapellido}",
        })
 
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})
    
@require_POST
def baja_veterinario(request, folio):
    from .services import dar_de_baja_veterinario
    try:
        ok, error = dar_de_baja_veterinario(folio)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})

#------------------------------------------ E S P E C I A L I D A D ------------------------------------------------------------#

@require_POST
def nueva_especialidad(request):
    from .services import validar_datos_especialidad, crear_especialidad_db
    try:
        data = {
            'clave': request.POST.get('clave', ''),
            'nombre': request.POST.get('nombre', ''),
            'descripcion': request.POST.get('descripcion', ''),
        }
 
        ok, error = validar_datos_especialidad(data)
        if not ok:
            return JsonResponse({'ok': False, 'error': error})
 
        esp = crear_especialidad_db(data)
        return JsonResponse({
            'ok': True,
            'clave': esp.clave,
            'nombre': esp.nombre,
        })
 
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'})

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

