# web/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date, timedelta
# Importa solo los que necesites para la lista por ahora:
from .models import Mascota, Propietario, Especie, Raza, Servicio, Medicamento, Usuario,Veterinario, Recepcionista, Administrador, Cita, Hospitalizacion, SignosVitales, Pago, EdoCita, ServCons, ServHosp, Consulta

from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, Min, Max, Q
from django.db.models.functions import TruncMonth, TruncDate
from django.http import HttpResponse
from django.template.loader import render_to_string
from functools import wraps
from collections import defaultdict
import json

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
#------------------------------------------ REPORTES ------------------------------------------------------------#

@login_required
def reportes(request):
    
    hoy = date.today()
    
    contexto = {
        'seccion_activa': 'reportes',
        'hoy': hoy
    }
    
    return render(request, 'reportes/reportes.html', contexto)

# =============================================================================


# Importa tus modelos — ajusta el path según tu estructura de app
# from .models import (Cita, Consulta, Hospitalizacion, Pago, Mascota,
#                      Propietario, Especie, Veterinario, EdoCita, EdoHosp,
#                      ServCons, ServHosp, Tratamiento)


# =============================================================================
#  DECORADOR: Solo administradores (tipo ADM)
# =============================================================================

def solo_admin(view_func):
    """
    Restringe acceso a usuarios cuyo Usuario.tipo.codigo == 'ADM'.
    Redirige al dashboard si no cumple la condición.
    Úsalo siempre DEBAJO de @login_required.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        try:
            # Busca el Usuario ligado al user de Django
            from .models import Usuario
            u = Usuario.objects.select_related('tipo').get(pk=request.user.pk)
            if u.tipo.codigo != 'ADM':
                return redirect('dashboard')
        except Exception:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


# =============================================================================
#  HELPERS
# =============================================================================

def _parse_rango(request, dias_default=30):
    """Lee fecha_inicio / fecha_fin del GET. Fallback: últimos N días."""
    hoy = date.today()
    try:
        fi = date.fromisoformat(request.GET.get('fecha_inicio', ''))
    except ValueError:
        fi = hoy - timedelta(days=dias_default)
    try:
        ff = date.fromisoformat(request.GET.get('fecha_fin', ''))
    except ValueError:
        ff = hoy
    return (fi, ff) if fi <= ff else (ff, fi)


def _json_mes(qs, x_key='mes', y_key='total'):
    """Serializa queryset con campo TruncMonth a JSON para Chart.js."""
    return json.dumps([
        {'mes': r[x_key].strftime('%b %Y'), 'total': float(r[y_key] or 0)}
        for r in qs
    ])


def _json_dia(qs, x_key='dia', y_key='total'):
    return json.dumps([
        {'dia': r[x_key].strftime('%d/%m'), 'total': float(r[y_key] or 0)}
        for r in qs
    ])


def _pdf_response(request, template, ctx):
    """Genera PDF con WeasyPrint a partir de un template HTML."""
    try:
        import weasyprint
    except ImportError:
        return HttpResponse(
            "WeasyPrint no instalado. Ejecuta: pip install weasyprint",
            status=500,
            content_type='text/plain'
        )
    html  = render_to_string(template, ctx, request=request)
    pdf   = weasyprint.HTML(string=html,
                             base_url=request.build_absolute_uri('/')).write_pdf()
    fname = ctx.get('titulo', 'reporte').lower().replace(' ', '_')
    resp  = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{fname}.pdf"'
    return resp


# =============================================================================
#  DASHBOARD HUB
# =============================================================================

@login_required
@solo_admin
def reportes(request):
    hoy       = date.today()
    mes_ini   = hoy.replace(day=1)
    kpis = {
        'citas_mes':      Cita.objects.filter(fecha__gte=mes_ini).count(),
        'ingresos_mes':   Pago.objects.filter(fecha__gte=mes_ini)
                              .aggregate(t=Sum('pagofinal'))['t'] or 0,
        'hosp_activas':   Hospitalizacion.objects.filter(fechaalta__isnull=True).count(),
        'mascotas_total': Mascota.objects.count(),
    }
    return render(request, 'reportes/reportes.html', {
        'seccion_activa': 'reportes', 'hoy': hoy, **kpis
    })


# =============================================================================
#  R1 · Citas por fecha, estado y veterinario
# =============================================================================

@login_required
@solo_admin
def reporte_citas(request):
    fi, ff    = _parse_rango(request)
    vet_id    = request.GET.get('veterinario', '')
    estado_id = request.GET.get('estado', '')

    qs = (Cita.objects
          .select_related('veterinario', 'estado', 'mascota__propietario')
          .filter(fecha__gte=fi, fecha__lte=ff))
    if vet_id:    qs = qs.filter(veterinario__folio=vet_id)
    if estado_id: qs = qs.filter(estado__clave=estado_id)

    por_estado = list(qs.values('estado__nombre')
                        .annotate(total=Count('folio')).order_by('-total'))
    por_vet    = list(qs.values('veterinario__nombrepila', 'veterinario__primerapellido')
                        .annotate(total=Count('folio')).order_by('-total'))
    tendencia  = (qs.annotate(mes=TruncMonth('fecha'))
                    .values('mes').annotate(total=Count('folio')).order_by('mes'))

    ctx = dict(
        seccion_activa='reportes', tipo_reporte='citas',
        titulo='Citas por fecha, estado y veterinario',
        fi=fi, ff=ff, vet_id=vet_id, estado_id=estado_id,
        veterinarios=Veterinario.objects.all().order_by('primerapellido'),
        estados=EdoCita.objects.all(),
        citas=qs.order_by('-fecha', '-hora'),
        total=qs.count(),
        por_estado=por_estado, por_vet=por_vet,
        chart_estados=json.dumps([{'label': r['estado__nombre'], 'val': r['total']}
                                   for r in por_estado]),
        chart_tendencia=_json_mes(tendencia),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/citas.html', ctx)
    return render(request, 'reportes/reporte_citas.html', ctx)


# =============================================================================
#  R2 · Hospitalizaciones
# =============================================================================

@login_required
@solo_admin
def reporte_hospitalizaciones(request):
    fi, ff    = _parse_rango(request)
    vet_id    = request.GET.get('veterinario', '')
    estado_id = request.GET.get('estado', '')

    qs = (Hospitalizacion.objects
          .select_related('veterinario', 'estado', 'expediente__mascota__propietario')
          .filter(fechaingreso__gte=fi, fechaingreso__lte=ff))
    if vet_id:    qs = qs.filter(veterinario__folio=vet_id)
    if estado_id: qs = qs.filter(estado__clave=estado_id)

    activas  = qs.filter(fechaalta__isnull=True).count()
    con_alta = qs.filter(fechaalta__isnull=False).count()
    ingresos = qs.aggregate(t=Sum('total'))['t'] or 0

    durs = [(h.fechaalta - h.fechaingreso).days
            for h in qs.filter(fechaalta__isnull=False)]
    dur_prom = round(sum(durs) / len(durs), 1) if durs else 0

    por_vet   = list(qs.values('veterinario__nombrepila', 'veterinario__primerapellido')
                       .annotate(total=Count('numero'), ing=Sum('total')).order_by('-total'))
    tendencia = (qs.annotate(mes=TruncMonth('fechaingreso'))
                   .values('mes').annotate(total=Count('numero')).order_by('mes'))

    from .models import EdoHosp
    ctx = dict(
        seccion_activa='reportes', tipo_reporte='hospitalizaciones',
        titulo='Reporte de hospitalizaciones',
        fi=fi, ff=ff, vet_id=vet_id, estado_id=estado_id,
        veterinarios=Veterinario.objects.all().order_by('primerapellido'),
        estados=EdoHosp.objects.all(),
        hospitalizaciones=qs.order_by('-fechaingreso'),
        total=qs.count(), activas=activas, con_alta=con_alta,
        ingresos=ingresos, dur_prom=dur_prom,
        por_vet=por_vet,
        chart_tendencia=_json_mes(tendencia),
        chart_vet=json.dumps([
            {'label': r['veterinario__nombrepila'][0] + '. ' + r['veterinario__primerapellido'],
             'val': r['total']} for r in por_vet]),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/hospitalizaciones.html', ctx)
    return render(request, 'reportes/reporte_hospitalizaciones.html', ctx)


# =============================================================================
#  R3 · Mascotas y propietarios
# =============================================================================

@login_required
@solo_admin
def reporte_mascotas(request):
    por_especie = list(Mascota.objects.values('especie__nombre')
                       .annotate(total=Count('folio')).order_by('-total'))
    por_estado  = list(Mascota.objects.values('estado__nombre')
                       .annotate(total=Count('folio')).order_by('-total'))
    por_sexo    = list(Mascota.objects.values('sexo').annotate(total=Count('folio')))
    top_prop    = (Propietario.objects
                   .annotate(num=Count('mascota')).order_by('-num')[:10])
    nuevas = (Mascota.objects
              .filter(expediente__fechaapertura__gte=date.today() - timedelta(days=365))
              .annotate(mes=TruncMonth('expediente__fechaapertura'))
              .values('mes').annotate(total=Count('folio')).order_by('mes'))

    ctx = dict(
        seccion_activa='reportes', tipo_reporte='mascotas',
        titulo='Mascotas y propietarios',
        por_especie=por_especie, por_estado=por_estado,
        por_sexo=por_sexo, top_prop=top_prop,
        total_mascotas=Mascota.objects.count(),
        total_propietarios=Propietario.objects.count(),
        chart_especies=json.dumps([{'label': r['especie__nombre'], 'val': r['total']}
                                    for r in por_especie]),
        chart_nuevas=_json_mes(nuevas),
        chart_sexo=json.dumps([
            {'label': 'Macho' if r['sexo'] == 'M' else 'Hembra' if r['sexo'] == 'H' else r['sexo'],
             'val': r['total']} for r in por_sexo]),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/mascotas.html', ctx)
    return render(request, 'reportes/reporte_mascotas.html', ctx)


# =============================================================================
#  R4 · Demografía de mascotas
# =============================================================================

@login_required
@solo_admin
def reporte_demografia(request):
    especie_id = request.GET.get('especie', '')
    qs = Mascota.objects.select_related('especie', 'raza')
    if especie_id:
        qs = qs.filter(especie__clave=especie_id)

    por_raza = list(qs.values('raza__nombre', 'especie__nombre')
                     .annotate(total=Count('folio')).order_by('-total')[:15])

    hoy = date.today()
    rangos = defaultdict(int)
    edades = []
    for m in qs.only('fechanacimiento'):
        try:
            edad = (hoy - m.fechanacimiento).days // 365
            edades.append(edad)
            if edad < 1:    rangos['< 1 año']   += 1
            elif edad < 3:  rangos['1–2 años']   += 1
            elif edad < 7:  rangos['3–6 años']   += 1
            elif edad < 12: rangos['7–11 años']  += 1
            else:           rangos['12+ años']   += 1
        except Exception:
            pass

    peso_prom = qs.aggregate(p=Avg('peso'))['p'] or 0

    ctx = dict(
        seccion_activa='reportes', tipo_reporte='demografia',
        titulo='Demografía de mascotas',
        especies=Especie.objects.all().order_by('nombre'),
        especie_id=especie_id,
        por_raza=por_raza, rangos_edad=dict(rangos),
        edad_promedio=round(sum(edades) / len(edades), 1) if edades else 0,
        peso_promedio=round(float(peso_prom), 2),
        total=qs.count(),
        chart_razas=json.dumps([{'label': r['raza__nombre'], 'val': r['total']}
                                  for r in por_raza]),
        chart_edades=json.dumps([{'label': k, 'val': v} for k, v in rangos.items()]),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/demografia.html', ctx)
    return render(request, 'reportes/reporte_demografia.html', ctx)


# =============================================================================
#  R5 · Servicios más vendidos
# =============================================================================

@login_required
@solo_admin
def reporte_servicios_top(request):
    fi, ff = _parse_rango(request)

    s_cons = list(ServCons.objects
                  .filter(consulta__cita__fecha__gte=fi, consulta__cita__fecha__lte=ff)
                  .values('servicio__clave', 'servicio__nombre', 'servicio__costo')
                  .annotate(usos=Count('id'), ingresos=Sum('subtotal'))
                  .order_by('-usos')[:15])
    s_hosp = list(ServHosp.objects
                  .filter(hospitalizacion__fechaingreso__gte=fi,
                          hospitalizacion__fechaingreso__lte=ff)
                  .values('servicio__clave', 'servicio__nombre')
                  .annotate(usos=Count('id'), ingresos=Sum('subtotal'))
                  .order_by('-usos')[:10])

    global_map = defaultdict(lambda: {'nombre': '', 'usos': 0, 'ingresos': 0.0})
    for r in s_cons:
        k = r['servicio__clave']
        global_map[k]['nombre']    = r['servicio__nombre']
        global_map[k]['usos']     += r['usos']
        global_map[k]['ingresos'] += float(r['ingresos'] or 0)
    for r in s_hosp:
        k = r['servicio__clave']
        global_map[k]['nombre']    = r['servicio__nombre']
        global_map[k]['usos']     += r['usos']
        global_map[k]['ingresos'] += float(r['ingresos'] or 0)
    ranking = sorted(global_map.values(), key=lambda x: x['usos'], reverse=True)[:10]

    ctx = dict(
        seccion_activa='reportes', tipo_reporte='servicios_top',
        titulo='Servicios más vendidos',
        fi=fi, ff=ff, s_cons=s_cons, s_hosp=s_hosp, ranking=ranking,
        chart_ranking=json.dumps([
            {'label': r['nombre'][:22], 'usos': r['usos'], 'ingresos': r['ingresos']}
            for r in ranking]),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/servicios_top.html', ctx)
    return render(request, 'reportes/reporte_servicios_top.html', ctx)


# =============================================================================
#  R6 · Tasa de retención de clientes
# =============================================================================

@login_required
@solo_admin
def reporte_retencion(request):
    hoy   = date.today()
    datos = []
    for i in range(11, -1, -1):
        # mes actual del loop
        primer_dia = (hoy.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        if primer_dia.month == 12:
            ultimo_dia = primer_dia.replace(day=31)
        else:
            ultimo_dia = (primer_dia.replace(month=primer_dia.month + 1, day=1)
                          - timedelta(days=1))
        # mes anterior
        ant_fin = primer_dia - timedelta(days=1)
        ant_ini = ant_fin.replace(day=1)

        props_ant = set(Cita.objects.filter(fecha__gte=ant_ini, fecha__lte=ant_fin)
                        .values_list('propietario__folio', flat=True))
        props_act = set(Cita.objects.filter(fecha__gte=primer_dia, fecha__lte=ultimo_dia)
                        .values_list('propietario__folio', flat=True))

        retenidos = len(props_ant & props_act)
        nuevos    = len(props_act - props_ant)
        perdidos  = len(props_ant - props_act)
        tasa      = round(retenidos / len(props_ant) * 100, 1) if props_ant else 0

        datos.append({
            'mes': primer_dia.strftime('%b %Y'),
            'retenidos': retenidos, 'nuevos': nuevos,
            'perdidos': perdidos,   'tasa': tasa,
            'total_act': len(props_act),
        })

    ultimos6  = [d['tasa'] for d in datos[-6:] if d['tasa'] > 0]
    tasa_prom = round(sum(ultimos6) / len(ultimos6), 1) if ultimos6 else 0

    ctx = dict(
        seccion_activa='reportes', tipo_reporte='retencion',
        titulo='Tasa de retención de clientes',
        datos=datos, tasa_prom=tasa_prom,
        chart_retencion=json.dumps([
            {'mes': d['mes'], 'tasa': d['tasa'], 'nuevos': d['nuevos']}
            for d in datos]),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/retencion.html', ctx)
    return render(request, 'reportes/reporte_retencion.html', ctx)


# =============================================================================
#  R7 · Ingresos por servicio
# =============================================================================

@login_required
@solo_admin
def reporte_ingresos_servicio(request):
    fi, ff = _parse_rango(request)

    ing_cons = list(ServCons.objects
                    .filter(consulta__cita__fecha__gte=fi, consulta__cita__fecha__lte=ff)
                    .values('servicio__clave', 'servicio__nombre', 'servicio__costo')
                    .annotate(usos=Count('id'), total=Sum('subtotal'))
                    .order_by('-total'))
    ing_hosp = list(ServHosp.objects
                    .filter(hospitalizacion__fechaingreso__gte=fi,
                            hospitalizacion__fechaingreso__lte=ff)
                    .values('servicio__clave', 'servicio__nombre')
                    .annotate(usos=Count('id'), total=Sum('subtotal'))
                    .order_by('-total'))

    total_cons = sum(float(r['total'] or 0) for r in ing_cons)
    total_hosp = sum(float(r['total'] or 0) for r in ing_hosp)
    gran_total = total_cons + total_hosp

    ing_mes = (Pago.objects
               .filter(fecha__gte=fi, fecha__lte=ff)
               .annotate(mes=TruncMonth('fecha'))
               .values('mes').annotate(total=Sum('pagofinal')).order_by('mes'))

    global_svc = defaultdict(float)
    for r in ing_cons: global_svc[r['servicio__nombre']] += float(r['total'] or 0)
    for r in ing_hosp: global_svc[r['servicio__nombre']] += float(r['total'] or 0)
    top8 = sorted(global_svc.items(), key=lambda x: x[1], reverse=True)[:8]

    ctx = dict(
        seccion_activa='reportes', tipo_reporte='ingresos_servicio',
        titulo='Ingresos por servicio',
        fi=fi, ff=ff,
        ing_cons=ing_cons, ing_hosp=ing_hosp,
        total_cons=total_cons, total_hosp=total_hosp, gran_total=gran_total,
        chart_tendencia=_json_mes(ing_mes),
        chart_dist=json.dumps([{'label': k[:20], 'val': v} for k, v in top8]),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/ingresos_servicio.html', ctx)
    return render(request, 'reportes/reporte_ingresos_servicio.html', ctx)


# =============================================================================
#  R8 · Carga laboral veterinaria
# =============================================================================

@login_required
@solo_admin
def reporte_carga_laboral(request):
    fi, ff = _parse_rango(request)

    citas_vet = list(Cita.objects
                     .filter(fecha__gte=fi, fecha__lte=ff)
                     .values('veterinario__folio', 'veterinario__nombrepila',
                             'veterinario__primerapellido',
                             'veterinario__especialidad__nombre')
                     .annotate(total_citas=Count('folio'))
                     .order_by('-total_citas'))

    consultas_vet = {
        r['cita__veterinario__folio']: r['total']
        for r in Consulta.objects
        .filter(cita__fecha__gte=fi, cita__fecha__lte=ff)
        .values('cita__veterinario__folio').annotate(total=Count('numero'))
    }
    hosp_vet = {
        r['veterinario__folio']: r['total']
        for r in Hospitalizacion.objects
        .filter(fechaingreso__gte=fi, fechaingreso__lte=ff)
        .values('veterinario__folio').annotate(total=Count('numero'))
    }

    for row in citas_vet:
        f = row['veterinario__folio']
        row['consultas']         = consultas_vet.get(f, 0)
        row['hospitalizaciones'] = hosp_vet.get(f, 0)
        row['carga_total']       = row['total_citas'] + row['hospitalizaciones']

    citas_dia = list(Cita.objects
                     .filter(fecha__gte=fi, fecha__lte=ff)
                     .annotate(dia=TruncDate('fecha'))
                     .values('dia').annotate(total=Count('folio')).order_by('dia'))

    ctx = dict(
        seccion_activa='reportes', tipo_reporte='carga_laboral',
        titulo='Carga laboral veterinaria',
        fi=fi, ff=ff, citas_vet=citas_vet,
        total_citas=sum(r['total_citas'] for r in citas_vet),
        chart_barras=json.dumps([
            {'label': r['veterinario__nombrepila'][0] + '. ' + r['veterinario__primerapellido'],
             'citas': r['total_citas'], 'hosp': r['hospitalizaciones']}
            for r in citas_vet]),
        chart_linea=json.dumps([
            {'dia': r['dia'].strftime('%d/%m'), 'total': r['total']}
            for r in citas_dia]),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/carga_laboral.html', ctx)
    return render(request, 'reportes/reporte_carga_laboral.html', ctx)


# =============================================================================
#  R9 · Citas por mes
# =============================================================================

@login_required
@solo_admin
def reporte_citas_mes(request):
    anio   = int(request.GET.get('anio', date.today().year))
    vet_id = request.GET.get('veterinario', '')

    qs = Cita.objects.filter(fecha__year=anio)
    if vet_id:
        qs = qs.filter(veterinario__folio=vet_id)

    por_mes_qs = (qs.annotate(mes=TruncMonth('fecha'))
                    .values('mes')
                    .annotate(
                        total=Count('folio'),
                        completadas=Count('folio', filter=Q(estado__nombre__icontains='complet')),
                        canceladas=Count('folio',  filter=Q(estado__nombre__icontains='cancel')),
                    ).order_by('mes'))

    por_mes = [
        {'mes_str': r['mes'].strftime('%B'), 'mes_num': r['mes'].month,
         'total': r['total'], 'completadas': r['completadas'],
         'canceladas': r['canceladas']}
        for r in por_mes_qs
    ]

    total_anual  = sum(r['total'] for r in por_mes)
    prom_mensual = round(total_anual / 12, 1)
    mes_pico     = max(por_mes, key=lambda x: x['total'], default=None)

    por_estado = list(qs.values('estado__nombre')
                        .annotate(total=Count('folio')).order_by('-total'))

    ctx = dict(
        seccion_activa='reportes', tipo_reporte='citas_mes',
        titulo=f'Citas por mes — {anio}',
        anio=anio,
        anios=list(range(date.today().year, date.today().year - 5, -1)),
        veterinarios=Veterinario.objects.all().order_by('primerapellido'),
        vet_id=vet_id, por_mes=por_mes, por_estado=por_estado,
        total_anual=total_anual, prom_mensual=prom_mensual, mes_pico=mes_pico,
        chart_mes=json.dumps([
            {'mes': r['mes_str'][:3], 'total': r['total'],
             'completadas': r['completadas'], 'canceladas': r['canceladas']}
            for r in por_mes]),
        chart_estado=json.dumps([
            {'label': r['estado__nombre'], 'val': r['total']}
            for r in por_estado]),
    )
    if request.GET.get('pdf'):
        return _pdf_response(request, 'reportes/pdf/citas_mes.html', ctx)
    return render(request, 'reportes/reporte_citas_mes.html', ctx)




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
