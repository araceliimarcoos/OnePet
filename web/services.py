from datetime import datetime

from .models import Propietario, Telefono, Medicamento, Servicio, Especie, Raza, Cita, Mascota, Veterinario, EdoCita, Especialidad, EdoUsuario, Usuario, Consulta, Expediente, Receta, Tratamiento, Hospitalizacion, EdoHosp, ServCons, ServHosp, SignosVitales, Pago, TipoUsuario
from django.utils import timezone
from datetime import date, time, datetime, timedelta
import re, json
from django.db import connection
from django.db import transaction


from .utils.validaciones import (
    validar_texto,
    validar_telefono,
    validar_email,
    formatear_texto,
    limpiar_espacios
)
#----------------------------------------------------------------- P R O P I E T A R I O S -----------------------------------------------------------------------------------

def generar_folio():
    folios = Propietario.objects.values_list('folio', flat=True)

    max_num = 0
    for f in folios:
        try:
            num = int(f.split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue

    return f"P-{max_num + 1:05d}"


def validar_datos(data):
    #  Campos obligatorios
    campos = {
        'nombre': 'Nombre',
        'apellido_paterno': 'Apellido paterno',
        'correo': 'Correo',
        'tel_principal': 'Teléfono principal',
        'calle': 'Calle',
        'numero': 'Número',
        'colonia': 'Colonia'
    }

    for key, nombre in campos.items():
        if not data.get(key):
            return False, f'El campo "{nombre}" es obligatorio'

    # Validar nombre
    ok, msg = validar_texto(data.get('nombre'), "nombre")
    if not ok:
        return False, msg

    ok, msg = validar_texto(data.get('apellido_paterno'), "apellido paterno")
    if not ok:
        return False, msg

    # Email
    ok, msg = validar_email(data.get('correo'))
    if not ok:
        return False, msg

    # Teléfono principal
    tel = data.get('tel_principal', '')
    ok, msg = validar_telefono(tel)
    if not ok:
        return False, msg

    return True, None

from django.contrib.auth.hashers import make_password

@transaction.atomic
def crear_propietario_db(data):

    propietario = Propietario.objects.create(
        folio=generar_folio(),

        nombrepila=formatear_texto(data.get('nombre')),
        primerapellido=formatear_texto(data.get('apellido_paterno')),
        segundoapellido=formatear_texto(data.get('apellido_materno') or ''),

        dircalle=formatear_texto(data.get('calle')),
        dirnum=data.get('numero'),
        dircolonia=formatear_texto(data.get('colonia')),

        correo=data.get('correo').strip().lower()
    )

    Telefono.objects.create(
        numprincipal=formatear_telefono(limpiar_espacios(data.get('tel_principal'))),
        numsecundario=formatear_telefono(limpiar_espacios(data.get('tel_secundario')))
            if data.get('tel_secundario') else None,
        propietario=propietario
    )
    
    tipo_prop = TipoUsuario.objects.get(codigo='PRO')  # 👈 ajusta si usas otro código
    estado_act = EdoUsuario.objects.get(clave='A')

    Usuario.objects.create(
        usuario=propietario.folio,
        contrasena=('12345'),
        tipo=tipo_prop,
        propietario=propietario,
        estado=estado_act,
    )


    return propietario


def formatear_telefono(numero):
    if not numero:
        return None

    numeros = re.sub(r'\D', '', numero)

    if len(numeros) != 10:
        raise ValueError("El teléfono debe tener 10 dígitos")

    return f"({numeros[:3]}) {numeros[3:6]}-{numeros[6:]}"


#--------------------------------------------------------------------- M A S C O T A S ------------------------------------------------------------------------------------------------

from .models import Mascota, EdoMasc

def generar_folio_mascota():
    ultimo = Mascota.objects.order_by('-folio').first()

    if not ultimo:
        return "M-00001"

    try:
        num = int(ultimo.folio.split('-')[1])
    except:
        num = 0

    return f"M-{num + 1:05d}"

#--------------------------------------------- C I T A S -----------------------------------------------------------------------------------
def generar_folio_cita():
    # Folios: C-00001
    folios = Cita.objects.values_list('folio', flat=True)


    max_num = 0
    for f in folios:
        try:
            num = int(f.split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue

    return f"C-{max_num + 1:05d}"

def validar_datos_cita(data):
    propietario_folio = data.get('propietario', '').strip()
    mascota_folio     = data.get('mascota', '').strip()
    veterinario_folio = data.get('veterinario', '').strip()
    fecha_str         = data.get('fecha', '').strip()
    hora_str          = data.get('hora', '').strip()
    motivo            = data.get('motivo', '').strip()
    
    try:
        hora_nueva = datetime.strptime(hora_str, '%H:%M').time()
    except:
        return False, 'Formato de hora inválido'
    
    hora_apertura = time(8, 0)
    hora_cierre   = time(19, 30)
    
    if hora_nueva < hora_apertura or hora_nueva > hora_cierre:
        return False, 'El horario de citas es de 8:00 AM a 7:30 PM'
    
    if not propietario_folio:
        return False, 'Selecciona un propietario'
    
    if not mascota_folio:
        return False, 'Selecciona una mascota'
    
    if not veterinario_folio:
        return False, 'Selecciona un veterinario'
    
    if not fecha_str:
        return False, 'La fecha es obligatoria'
    
    if not hora_str:
        return False, 'La hora es obligatoria'
    
    if not motivo:
        return False, 'El motivo de la cita es obligatorio'
    
    if len(motivo) > 120:
        return False, 'El motivo no puede superar 120 caracteres'
 
    # La fecha no puede ser hoy ni en el pasado
    try:
        from datetime import date
        fecha = date.fromisoformat(fecha_str)
        if fecha <= date.today():
            return False, 'La fecha debe ser a partir de mañana'
    except ValueError:
        return False, 'Formato de fecha inválido'
 
    # Verificar que no haya otra cita con el mismo vet, fecha y hora, Verifica rango de 30 minutos
    hora_nueva  = datetime.strptime(hora_str, '%H:%M').time()
    dt_nueva    = datetime.combine(date.today(), hora_nueva)
    hora_min    = (dt_nueva - timedelta(minutes=30)).time()
    hora_max    = (dt_nueva + timedelta(minutes=30)).time()
    
    conflicto = Cita.objects.filter(
        veterinario__folio=veterinario_folio,
        fecha=fecha_str,
        hora__gt=hora_min,
        hora__lt=hora_max,
    ).exclude(estado__nombre='Cancelada')  # las canceladas no bloquean el horario
    
    if conflicto.exists():
        cita_conf = conflicto.first()
        return False, f'El veterinario ya tiene una cita a las {cita_conf.hora.strftime("%H:%M")} — debe haber al menos 30 minutos de diferencia'
 
    return True, None

def crear_cita_db(data):
    propietario = Propietario.objects.get(folio=data['propietario'])
    mascota     = Mascota.objects.get(folio=data['mascota'])
    veterinario = Veterinario.objects.get(folio=data['veterinario'])
    estado      = EdoCita.objects.get(nombre='Pendiente')   # estado inicial
 
    cita = Cita.objects.create(
        folio=generar_folio_cita(),
        fecha=data['fecha'],
        hora=data['hora'],
        motivo=data['motivo'].strip(),
        propietario=propietario,
        mascota=mascota,
        veterinario=veterinario,
        estado=estado,
    )
    return cita

def validar_datos_editar_cita(data, folio_actual):
    if not data.get('fecha'):
        return False, 'La fecha es obligatoria'
    if not data.get('hora'):
        return False, 'La hora es obligatoria'
    if not data.get('veterinario'):
        return False, 'Selecciona un veterinario'
    if not data.get('estado'):
        return False, 'El estado es obligatorio'
    if not data.get('motivo', '').strip():
        return False, 'El motivo es obligatorio'

    try:
        fecha    = date.fromisoformat(data['fecha'])
        if fecha < date.today():
            return False, 'La fecha no puede ser anterior a hoy'
        
        hora_str = data['hora']

        hora_nueva = datetime.strptime(hora_str, '%H:%M').time()
        dt_nueva   = datetime.combine(date.today(), hora_nueva)
        hora_min   = (dt_nueva - timedelta(minutes=30)).time()
        hora_max   = (dt_nueva + timedelta(minutes=30)).time()

        conflicto = Cita.objects.filter(
            veterinario__folio=data['veterinario'],
            fecha=data['fecha'],
            hora__gt=hora_min,
            hora__lt=hora_max,
        ).exclude(
            estado__nombre='Cancelada'  # las canceladas no bloquean el horario
        ).exclude(
            folio=folio_actual  # excluye la cita que se está editando
        )

        if conflicto.exists():
            cita_conf = conflicto.first()
            return False, f'El veterinario ya tiene una cita a las {cita_conf.hora.strftime("%H:%M")} — debe haber al menos 30 minutos de diferencia'

    except ValueError:
        return False, 'Formato de fecha u hora inválido'

    return True, None

#--------------------------------------------- C O N S U L T A S -----------------------------------------------------------------------------------
TEMP_MIN,  TEMP_MAX  = 35.0, 42.0   # °C
FC_MIN,    FC_MAX    = 20,   350     # lpm
FR_MIN,    FR_MAX    = 5,    120     # rpm

def validar_rango_signos(temp, fc, fr, requeridos=True):
    if requeridos:
        if temp <= 0: return False, 'La temperatura es obligatoria'
        if fc   <= 0: return False, 'La frecuencia cardíaca es obligatoria'
        if fr   <= 0: return False, 'La frecuencia respiratoria es obligatoria'

    if temp > 0 and not (TEMP_MIN <= temp <= TEMP_MAX):
        return False, f'La temperatura debe estar entre {TEMP_MIN} °C y {TEMP_MAX} °C (ingresado: {temp} °C)'
    if fc > 0 and not (FC_MIN <= fc <= FC_MAX):
        return False, f'La frecuencia cardíaca debe estar entre {FC_MIN} y {FC_MAX} lpm (ingresado: {fc} lpm)'
    if fr > 0 and not (FR_MIN <= fr <= FR_MAX):
        return False, f'La frecuencia respiratoria debe estar entre {FR_MIN} y {FR_MAX} rpm (ingresado: {fr} rpm)'

    return True, None

def validar_datos_consulta(data):
    sintomas    = data.get('sintomas', '').strip()
    diagnostico = data.get('diagnostico', '').strip()
    observaciones = data.get('observaciones', '').strip()
    peso = data.get('peso', 0)

    try:
        temp = float(data.get('temperatura', 0))
        fc   = int(data.get('freccardiaca',  0))
        fr   = int(data.get('frecrespiratoria', 0))
        peso = float(data.get('peso', 0))
    except (ValueError, TypeError):
        return False, 'Los signos vitales deben ser valores numéricos'
    
    if not sintomas:
        return False, 'Los síntomas son obligatorios'
    if len(sintomas) > 150:
        return False, 'Los síntomas no pueden superar 150 caracteres'
    if not diagnostico:
        return False, 'El diagnóstico es obligatorio'
    if len(diagnostico) > 150:
        return False, 'El diagnóstico no puede superar 150 caracteres'
    if not observaciones:
        return False, 'Las observaciones son obligatorias'
    ok, msg = validar_rango_signos(temp, fc, fr, requeridos=False)
    if not ok:
        return False, msg
    if peso <= 0:
        return False, 'El peso es obligatorio'
    
    medicamentos_list = _parsear_json(data.get('medicamentos_json', '[]'))
    for item in medicamentos_list:
        if len(item.get('notas', '')) > 50:
            return False, 'Las notas no del medicamento "{item.get("nombre")}" no pueden superar 50 caracteres'
        if len(item.get('dosis', '')) > 30:
            return False, f'La dosis de "{item.get("clave")}" no puede superar 30 caracteres'
        if len(item.get('frecuencia', '')) > 30:
            return False, f'La frecuencia de "{item.get("clave")}" no puede superar 30 caracteres'
        if len(item.get('duracion', '')) > 30:
            return False, f'La duración de "{item.get("clave")}" no puede superar 30 caracteres'
        
    return True, None

def guardar_consulta_db(cita, data):
    
    # 1. Expediente — crear si la mascota no tiene uno
    expediente, _ = Expediente.objects.get_or_create(
        mascota=cita.mascota,
        defaults={'fechaapertura': timezone.now().date()}
    )
    
    #Actualizar peso
    nuevo_peso = data.get('peso', '')
    if nuevo_peso:
        try:
            cita.mascota.peso = float(nuevo_peso)
            cita.mascota.save()
        except (ValueError, TypeError):
            pass
    
    # 2. Consulta
    consulta = Consulta.objects.create(
        sintomas=data['sintomas'].strip(),
        freccardiaca=int(data['freccardiaca']),
        frecrespiratoria=int(data['frecrespiratoria']),
        temperatura=float(data['temperatura']),
        observaciones=data['observaciones'].strip(),
        diagnostico=data['diagnostico'].strip(),
        total=0,
        cita=cita,
        expediente=expediente,
    )
    
    # 3. Marcar cita como Atendida
    try:
        cita.estado = EdoCita.objects.get(nombre='Atendida')
        cita.save()
    except EdoCita.DoesNotExist:
        pass
    
    # 4. Receta + Tratamientos
    medicamentos_list = _parsear_json(data.get('medicamentos_json', '[]'))
    if medicamentos_list:
        receta = Receta.objects.create(
            fecha=timezone.now().date(),
            instrugenerales=data.get('instrugenerales', '').strip() or 'Ver indicaciones',
            consulta=consulta,
        )
        
        # Insertar tratamientos con SQL pa evitar el id
        with connection.cursor() as cursor:
            _insertar_tratamientos(cursor, receta.numero, medicamentos_list)
            
    # 5. Servicios extra
    servicios_list = _parsear_json(data.get('servicios_json', '[]'))
    if servicios_list:
        with connection.cursor() as cursor:
            for item in servicios_list:
                try:
                    cantidad = int(item.get('cantidad', 1))
                    costo    = float(item.get('costo', 0))
                    cursor.execute("""
                        INSERT INTO serv_cons (servicio, consulta, cantidad, subtotal)
                        VALUES (%s, %s, %s, %s)
                    """, [item['clave'], consulta.numero, cantidad, round(cantidad * costo, 2)])
                except Exception as e:
                    print(f"[serv_cons INSERT error] {e}")
    # 6. Calcular y guardar total
    consulta.total = _calcular_total_consulta(consulta.numero)
    consulta.save()
                        
    return consulta

def actualizar_consulta_db(consulta, data):
    """Edita sintomas, diagnostico y observaciones de una consulta existente."""
    consulta.sintomas     = data['sintomas'].strip()
    consulta.diagnostico  = data['diagnostico'].strip()
    consulta.observaciones = data['observaciones'].strip()
    consulta.save()
    return consulta

def guardar_servicios_consulta(consulta, servicios_json_str):
    """Inserta filas en serv_cons usando SQL directo (tabla compuesta sin id en Django)."""
    try:
        servicios_list = json.loads(servicios_json_str)
    except (json.JSONDecodeError, TypeError):
        return
    
    if not servicios_list:
        return
    
    with connection.cursor() as cursor:
        for item in servicios_list:
            try:
                cantidad = int(item.get('cantidad', 1))
                costo    = float(item.get('costo', 0))
                subtotal = round(cantidad * costo, 2)
                cursor.execute("""
                    INSERT INTO serv_cons (servicio, consulta, cantidad, subtotal)
                    VALUES (%s, %s, %s, %s)
                """, [
                    item['clave'],
                    consulta.numero,
                    cantidad,
                    subtotal,
                ])
            except (KeyError, ValueError):
                continue

def obtener_servicios_consulta(consulta_numero):
    """Lee serv_cons con SQL directo."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.clave, s.nombre, s.descripcion, s.costo,
                   sc.cantidad, sc.subtotal
            FROM serv_cons sc
            JOIN servicio s ON sc.servicio = s.clave
            WHERE sc.consulta = %s
        """, [consulta_numero])
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

# ── FUNCIONES AUXILIARES ──────────────────────────────────────────────────
def _parsear_json(json_str):
    try:
        result = json.loads(json_str)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
 
 
def _calcular_total_consulta(consulta_numero):
    """
    Total = suma de serv_cons.subtotal + suma de (tratamiento.cantidad * medicamento.precio)
    """
    with connection.cursor() as cursor:
        # Servicios
        cursor.execute("""
            SELECT COALESCE(SUM(sc.subtotal), 0)
            FROM serv_cons sc
            WHERE sc.consulta = %s
        """, [consulta_numero])
        total_servicios = float(cursor.fetchone()[0])
 
        # Medicamentos (de la receta asociada a esta consulta)
        cursor.execute("""
            SELECT COALESCE(SUM(t.cantidad * m.precio), 0)
            FROM tratamiento t
            JOIN medicamento m ON t.medicamento = m.clave
            JOIN receta r ON t.receta = r.numero
            WHERE r.consulta = %s
        """, [consulta_numero])
        total_medicamentos = float(cursor.fetchone()[0])
 
    return round(total_servicios + total_medicamentos, 2)
 
 
def _calcular_total_hospitalizacion(hosp_numero):
    """
    Total = días hospitalizados (registros únicos en signos_vitales)
            + serv_hosp.subtotal
            + (tratamiento.cantidad * medicamento.precio)
 
    Nota: el costo por día se toma como la suma de servicios de hospitalización
    dividida entre los días, a menos que haya una tarifa fija definida.
    Por ahora: total = serv_hosp + medicamentos.
    Los días se calculan como (fechaalta - fechaingreso).days + 1 (informativo).
    """
    with connection.cursor() as cursor:
        # Servicios de hospitalización
        cursor.execute("""
            SELECT COALESCE(SUM(subtotal), 0)
            FROM serv_hosp
            WHERE hospitalizacion = %s
        """, [hosp_numero])
        total_servicios = float(cursor.fetchone()[0])
 
        # Medicamentos
        cursor.execute("""
            SELECT COALESCE(SUM(t.cantidad * m.precio), 0)
            FROM tratamiento t
            JOIN medicamento m ON t.medicamento = m.clave
            JOIN receta r ON t.receta = r.numero
            WHERE r.hospitalizacion = %s
        """, [hosp_numero])
        total_medicamentos = float(cursor.fetchone()[0])
 
        # Días registrados (informativo, incluido en el retorno si quieres mostrarlo)
        cursor.execute("""
            SELECT COUNT(DISTINCT fecha)
            FROM signos_vitales
            WHERE hospitalizacion = %s
        """, [hosp_numero])
        dias = cursor.fetchone()[0]
 
    return round(total_servicios + total_medicamentos, 2)

#--------------------------------------------- H O S P I T A L I Z A C I O N -----------------------------------------------------------------------------------
def validar_datos_hospitalizacion(data):
    diagno  = data.get('diagnoingreso', '').strip()
    obs     = data.get('obsergenerales', '').strip()
    vet     = data.get('veterinario', '').strip()
 
    if not diagno:
        return False, 'El diagnóstico de ingreso es obligatorio'
    if len(diagno) > 150:
        return False, 'El diagnóstico no puede superar 150 caracteres'
    if not obs:
        return False, 'Las observaciones generales son obligatorias'
    if len(obs) > 200:
        return False, 'Las observaciones no pueden superar 200 caracteres'
    if not vet:
        return False, 'El veterinario responsable es obligatorio'
 
    return True, None

def crear_hospitalizacion_db(consulta, data):
    
    # Crea la hospitalización a partir de una consulta existente.
 
    estado_inicial = EdoHosp.objects.filter(
        nombre__icontains='Hospitalizado'
    ).first() or EdoHosp.objects.first()
    
    veterinario = Veterinario.objects.get(folio=data['veterinario'])
    now = timezone.now()
 
    hosp = Hospitalizacion.objects.create(
        diagnoingreso=data['diagnoingreso'].strip(),
        fechaingreso=now.date(),
        horaingreso=now.time(),
        obsergenerales=data['obsergenerales'].strip(),
        fechaalta=None,
        horaalta=None,
        total=0,
        consulta=consulta,
        estado=estado_inicial,
        veterinario=veterinario,
        expediente=consulta.expediente,
    )
 
    # Signos vitales iniciales y peso actualizaod
    try:
        temp = float(data.get('temperatura', 0))
        fc   = int(data.get('freccardiaca', 0))
        fr   = int(data.get('frecrespiratoria', 0))
        if temp > 0 and fc > 0 and fr > 0:
            SignosVitales.objects.create(
                fecha=now.date(),
                freccardiaca=fc,
                frecrespiratoria=fr,
                temperatura=temp,
                hospitalizacion=hosp,
            )
    except (ValueError, TypeError):
        pass
    
    peso = data.get('peso','')
    if peso:
        try:
            hosp.expediente.mascota.peso = float(peso)
            hosp.expediente.mascota.save()
        except (ValueError, TypeError):
            pass
 
    # Receta + tratamientos
    medicamentos_list = _parsear_json(data.get('medicamentos_json', '[]'))
    if medicamentos_list:
        receta = Receta.objects.create(
            fecha=now.date(),
            instrugenerales=data.get('instrugenerales', '').strip() or 'Ver indicaciones',
            hospitalizacion=hosp,
        )
        with connection.cursor() as cursor:
            _insertar_tratamientos(cursor, receta.numero, medicamentos_list)
 
    # Servicios
    servicios_list = _parsear_json(data.get('servicios_json', '[]'))
    if servicios_list:
        with connection.cursor() as cursor:
            for item in servicios_list:
                try:
                    cantidad = int(item.get('cantidad', 1))
                    costo    = float(item.get('costo', 0))
                    cursor.execute("""
                        INSERT INTO serv_hosp (servicio, hospitalizacion, cantidad, subtotal)
                        VALUES (%s, %s, %s, %s)
                    """, [item['clave'], hosp.numero, cantidad, round(cantidad * costo, 2)])
                except Exception as e:
                    print(f"[serv_hosp INSERT error] {e}")
 
    return hosp

def actualizar_hospitalizacion_db(hosp, data):
    """
    Actualiza signos vitales del día, diagnóstico/observaciones,
    peso de la mascota, y agrega receta/servicios si se proporcionaron.
    """
    now = timezone.now()
 
    # Signos vitales del día
    try:
        temp = float(data.get('temperatura') or 0)
        fc   = int(data.get('freccardiaca') or 0)
        fr   = int(data.get('frecrespiratoria') or 0)
        if temp > 0 and fc > 0 and fr > 0:
            SignosVitales.objects.create(
                fecha=now.date(),
                freccardiaca=fc,
                frecrespiratoria=fr,
                temperatura=temp,
                hospitalizacion=hosp,
            )
    except (ValueError, TypeError):
        pass
 
    # Peso
    peso = data.get('peso', '')
    if peso:
        try:
            hosp.expediente.mascota.peso = float(peso)
            hosp.expediente.mascota.save()
        except (ValueError, TypeError):
            pass
 
    # Diagnóstico y observaciones (opcionales)
    diagno = data.get('diagnoingreso', '').strip()
    obs    = data.get('obsergenerales', '').strip()
    if diagno:
        hosp.diagnoingreso = diagno
    if obs:
        hosp.obsergenerales = obs
    hosp.save()
 
    # Receta: si ya existe, agregar más tratamientos; si no, crear nueva
    medicamentos_list = _parsear_json(data.get('medicamentos_json', '[]'))
    if medicamentos_list:
        receta = Receta.objects.filter(hospitalizacion=hosp).first()
        if not receta:
            receta = Receta.objects.create(
                fecha=now.date(),
                instrugenerales=data.get('instrugenerales', '').strip() or 'Ver indicaciones',
                hospitalizacion=hosp,
            )
        with connection.cursor() as cursor:
            _insertar_tratamientos(cursor, receta.numero, medicamentos_list)
 
    # Servicios extra
    servicios_list = _parsear_json(data.get('servicios_json', '[]'))
    if servicios_list:
        with connection.cursor() as cursor:
            for item in servicios_list:
                try:
                    cantidad = int(item.get('cantidad', 1))
                    costo    = float(item.get('costo', 0))
                    cursor.execute("""
                        INSERT INTO serv_hosp (servicio, hospitalizacion, cantidad, subtotal)
                        VALUES (%s, %s, %s, %s)
                    """, [item['clave'], hosp.numero, cantidad, round(cantidad * costo, 2)])
                except Exception as e:
                    print(f"[serv_hosp UPDATE INSERT error] {e}")
 
    return hosp

def dar_de_alta_hospitalizacion(hosp, data):
    now = timezone.now()
 
    estado_alta = EdoHosp.objects.filter(
        nombre__icontains='Alta'
    ).first() or EdoHosp.objects.last()
 
    hosp.fechaalta  = now.date()
    hosp.horaalta   = now.time()
    hosp.estado     = estado_alta
    hosp.total      = _calcular_total_hospitalizacion(hosp.numero)
    hosp.save()
    
    return hosp

def obtener_servicios_hosp(hosp_numero):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.clave, s.nombre, s.costo, sh.cantidad, sh.subtotal
            FROM serv_hosp sh
            JOIN servicio s ON sh.servicio = s.clave
            WHERE sh.hospitalizacion = %s
        """, [hosp_numero])
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
 
 
def obtener_signos_vitales(hosp_numero):
    vitales = SignosVitales.objects.filter(
        hospitalizacion__numero=hosp_numero
    ).order_by('-fecha')
    return vitales

# ── FUNCIÓN AUXILIAR: INSERT tratamiento (reutilizable) ───────────────────
def _insertar_tratamientos(cursor, receta_numero, medicamentos_list):
    # Obtener mascota desde la receta
    cursor.execute("""
        SELECT hospitalizacion, consulta FROM receta WHERE numero = %s
    """, [receta_numero])
    row = cursor.fetchone()
    hosp_id, consulta_id = row if row else (None, None)

    if hosp_id:
        cursor.execute("""
            SELECT e.mascota FROM hospitalizacion h
            JOIN expediente e ON h.expediente = e.mascota
            WHERE h.numero = %s
        """, [hosp_id])
    else:
        cursor.execute("""
            SELECT e.mascota FROM consulta c
            JOIN expediente e ON c.expediente = e.mascota
            WHERE c.numero = %s
        """, [consulta_id])

    mascota_row = cursor.fetchone()
    mascota_folio = mascota_row[0] if mascota_row else None

    for item in medicamentos_list:
        try:
            params = [
                receta_numero,
                item['clave'],
                int(item.get('cantidad', 1)),
                item.get('dosis', ''),
                item.get('frecuencia', ''),
                item.get('duracion', ''),
                item.get('notas', ''),
                mascota_folio,
                'Activo',
            ]
            print(f"[tratamiento params] {params}")  # ← para ver qué llega
            cursor.execute("""
                INSERT INTO tratamiento
                (receta, medicamento, cantidad, dosis, frecuencia, duracion, notas, mascota, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, params)
        except Exception as e:
            print(f"[tratamiento INSERT error] {e}")
            continue
#-------------------------------------------------------------------------------------------------------------------------------------
def validar_datos_mascota(data):
    
    campos = {
        'nombre': 'Nombre de la mascota',
        'sexo': 'Sexo',
        'fechanacimiento': 'Fecha de nacimiento',
        'especie': 'Especie',
        'raza': 'Raza',
        'propietario': 'Propietario'
    }

    for key, nombre in campos.items():
        if not data.get(key):
            return False, f'El campo "{nombre}" es obligatorio'

    ok, msg = validar_texto(data.get('nombre'), "nombre de la mascota")
    if not ok:
        return False, msg

    if data.get('sexo') not in ['M', 'H']:
        return False, "El sexo debe ser 'M' o 'H'"

    peso = data.get('peso')
    if peso:
        try:
            float(peso)
        except ValueError:
            return False, "El peso debe ser un número válido"

    return True, None

from datetime import datetime

def crear_mascota_db(data):
    # Usamos clave/folio para asegurar la relación
    
    especie = Especie.objects.get(clave=data.get('especie'))
    raza = Raza.objects.get(clave=data.get('raza'))
    propietario = Propietario.objects.get(folio=data.get('propietario'))

    estado_activo = EdoMasc.objects.get(clave='ACTV')
    folio_generado = generar_folio_mascota()

    # Manejo de fecha con limpieza de posibles espacios
    fecha_str = data.get('fechanacimiento')
    if fecha_str and fecha_str.strip():
        fecha = datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
    else:
        fecha = None

    # Limpieza de peso (por si llega cadena vacía)
    peso_raw = data.get('peso')
    peso_final = float(peso_raw) if peso_raw and str(peso_raw).strip() else None

    mascota = Mascota.objects.create(
        folio=folio_generado,
        nombre=formatear_texto(data.get('nombre')),
        sexo=data.get('sexo'),
        fechanacimiento=fecha,
        peso=peso_final,
        color=formatear_texto(data.get('color')) if data.get('color') else None,
        alergias=formatear_texto(data.get('alergias')) if data.get('alergias') else None,
        caracunica=formatear_texto(data.get('caracunica')) if data.get('caracunica') else None,
        especie=especie,
        raza=raza,
        propietario=propietario,
        estado=estado_activo
    )
    
    Expediente.objects.get_or_create(
    mascota=mascota,
    defaults={'fechaapertura': timezone.now().date()}
    )
    
    return mascota


#------------------------------------------------------------------ M E D I C A M E N T O S -----------------------------------------------------------------------------------
def generar_clave_medicamento():
    #claves : MED-001
    claves = Medicamento.objects.values_list('clave', flat=True)
    
    max_num = 0
    for c in claves:
        try:
            num = int(c.split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue

    return f"MED-{max_num + 1:03d}"

def validar_datos_medicamento(data):
    #  Campos obligatorios
    nombre = data.get('nombre', '').strip()
    precio = data.get('precio', '').strip()
    descripcion = data.get('descripcion', '').strip()
    
    if not nombre:
        return False, "El nombre del medicamento es obligatorio"
    
    if len(nombre) > 50:
        return False, "El nombre no puede superar 50 caracteres"
    
    if not precio:
        return False, "El precio es obligatorio"
    
    try:
        precio_num = float(precio)
        if precio_num < 0:
            return False, 'El precio no puede ser negativo'
    except ValueError:
        return False, 'El precio debe ser un número válido'
    
    
    if not descripcion:
        return False, "La descripción es obligatoria"

    if len(descripcion) > 90:
        return False, "La descripción no puede superar 90 caracteres"
    
    # Verifica que el med no este registrado ya
    if Medicamento.objects.filter(nombre__iexact=nombre).exists():
        return False, f'Ya existe un medicamento con el nombre "{nombre}"'
    
    return True, None

def crear_medicamento_db(data):
    #crea el med y lo guarda en la db
    medicamento = Medicamento.objects.create(
        clave=generar_clave_medicamento(),
        nombre = data.get('nombre').strip().title(),
        descripcion = data.get('descripcion').strip(),
        precio = float(data.get('precio')) 
    )
    return medicamento

#--------------------------------------------- S E R V I C I O S -----------------------------------------------------------------------------------
def generar_clave_servicio():
    #claves : SERV-01
    claves = Servicio.objects.values_list('clave', flat=True)
    
    max_num = 0
    for c in claves:
        try:
            num = int(c.split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue

    return f"SERV-{max_num + 1:02d}"

def validar_datos_servicio(data):
    #  Campos obligatorios
    nombre = data.get('nombre', '').strip()
    costo = data.get('costo', '').strip()
    descripcion = data.get('descripcion', '').strip()
    
    if not nombre:
        return False, "El nombre del servicio es obligatorio"
    
    if len(nombre) > 35:
        return False, "El nombre no puede superar 35 caracteres"
    
    if not costo:
        return False, "El costo es obligatorio"
    
    try:
        costo_num = float(costo)
        if costo_num < 0:
            return False, 'El costo no puede ser negativo'
    except ValueError:
        return False, 'El costo debe ser un número valido'
    
    if not descripcion:
        return False, "La descripción es obligatoria"

    if len(descripcion) > 150:
        return False, "La descripción no puede superar 150 caracteres"

    # Verifica que el servicios no este registrado ya
    if Servicio.objects.filter(nombre__iexact=nombre).exists():
        return False, f'Ya existe un servicio con el nombre "{nombre}"'
    
    return True, None

def crear_servicio_db(data):
    #crea el servicio y lo guarda en la db
    servicio = Servicio.objects.create(
        clave=generar_clave_servicio(),
        nombre = data.get('nombre').strip().title(),
        descripcion = data.get('descripcion').strip(),
        costo = float(data.get('costo')) 
    )
    return servicio

#--------------------------------------------- E S P E C I E S -----------------------------------------------------------------------------------

def generar_clave_especie():
    #claves : ESPE-01
    claves = Especie.objects.values_list('clave', flat=True)
    
    max_num = 0
    for c in claves:
        try:
            num = int(c.split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue

    return f"ESPE-{max_num + 1:02d}"

def validar_datos_especie(data):
    nombre = data.get('nombre', '').strip()
    
    if not nombre:
        return False, "El nombre de la especie es obligatorio"
    
    if len(nombre) > 25:
        return False, "El nombre no puede superar 25 caracteres"
    
    # Verifica que la especie no este registrado ya
    if Especie.objects.filter(nombre__iexact=nombre).exists():
        return False, f'Ya existe una especie con el nombre "{nombre}"'
    
    return True, None

def crear_especie_db(data):
    #crea la especie y lo guarda en la db
    especie = Especie.objects.create(
        clave=generar_clave_especie(),
        nombre = data.get('nombre').strip().title()
    )
    return especie

#--------------------------------------------- R A Z A S -----------------------------------------------------------------------------------
def generar_clave_raza():
    #claves : RAZ-001
    claves = Raza.objects.values_list('clave', flat=True)
    
    max_num = 0
    for c in claves:
        try:
            num = int(c.split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue

    return f"RAZ-{max_num + 1:03d}"

def validar_datos_raza(data):
    nombre =        data.get('nombre', '').strip()
    clave_especie = data.get('especie', '').strip()
    
    if not nombre:
        return False, "El nombre de la raza es obligatorio"
    
    if len(nombre) > 25:
        return False, "El nombre no puede superar 25 caracteres"
    
    if not clave_especie:
        return False, "La especie es obligatoria"
    
    if not Especie.objects.filter(clave=clave_especie).exists():
        return False, "La especie no existe"
    
    # Verifica que la raza no este registrado ya
    if Raza.objects.filter(nombre__iexact=nombre).exists():
        return False, f'Ya existe una raza con el nombre "{nombre}"'
    
    return True, None

def crear_raza_db(data):
    especie = Especie.objects.get(clave=data.get('especie'))
    
    #crea la raza y lo guarda en la db
    raza = Raza.objects.create(
        clave=generar_clave_raza(),
        nombre = data.get('nombre').strip().title(),
        especie = especie
    )
    return raza

#--------------------------------------------- V E T E R I N A R I O S -----------------------------------------------------------------------------------
def generar_folio_veterinario():
    # folios: VET-001
    folios = Veterinario.objects.values_list('folio', flat=True)
    
    max_num = 0
    for f in folios:
        try:
            num = int(f.split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue
 
    return f"VET-{max_num + 1:03d}"
 
def validar_datos_veterinario(data, folio_actual=None):
    import re
    from .models import Veterinario, Especialidad
 
    nombre    = data.get('nombre', '').strip()
    ap_pat    = data.get('apellido_paterno', '').strip()
    correo    = data.get('correo', '').strip()
    telefono  = re.sub(r'\D', '', data.get('telefono', ''))
    especialidad = data.get('especialidad', '').strip()
 
    if not nombre:
        return False, 'El nombre es obligatorio'
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
        return False, 'El nombre solo debe contener letras'
 
    if not ap_pat:
        return False, 'El apellido paterno es obligatorio'
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', ap_pat):
        return False, 'El apellido paterno solo debe contener letras'
 
    if not correo:
        return False, 'El correo es obligatorio'
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', correo.lower()):
        return False, 'El formato del correo no es válido'
 
    qs_correo = Veterinario.objects.filter(correo__iexact=correo)
    if folio_actual:
        qs_correo = qs_correo.exclude(folio=folio_actual)
    if qs_correo.exists():
        return False, f'El correo "{correo}" ya está registrado'
 
    if len(telefono) != 10:
        return False, 'El teléfono debe tener exactamente 10 dígitos'
 
    qs_tel = Veterinario.objects.filter(telefono__icontains=telefono)
    if folio_actual:
        qs_tel = qs_tel.exclude(folio=folio_actual)
    if qs_tel.exists():
        return False, 'Este número de teléfono ya está registrado'
 
    # Cédula solo se valida al CREAR (folio_actual=None)
    if not folio_actual:
        cedula = data.get('cedula', '').strip()
        if not cedula:
            return False, 'La cédula profesional es obligatoria'
        if not re.match(r'^\d{7,8}$', cedula):
            return False, 'La cédula debe tener 7 u 8 dígitos numéricos'
        if Veterinario.objects.filter(cedula=cedula).exists():
            return False, f'La cédula "{cedula}" ya está registrada'
 
    if not especialidad:
        return False, 'La especialidad es obligatoria'
    if not Especialidad.objects.filter(clave=especialidad).exists():
        return False, 'La especialidad seleccionada no existe'
 
    return True, None


@transaction.atomic
def crear_veterinario_db(data):
    numeros      = re.sub(r'\D', '', data.get('telefono', ''))
    tel_fmt      = f"({numeros[:3]}) {numeros[3:6]}-{numeros[6:]}"
    especialidad = Especialidad.objects.get(clave=data['especialidad'])
 
    veterinario = Veterinario.objects.create(
        folio=generar_folio_veterinario(),
        nombrepila=data['nombre'].strip().title(),
        primerapellido=data['apellido_paterno'].strip().title(),
        segundoapellido=data.get('apellido_materno', '').strip().title() or None,
        correo=data['correo'].strip().lower(),
        telefono=tel_fmt,
        cedula=data['cedula'].strip(),
        especialidad=especialidad,
    )
 
    # ── Crear usuario asociado automáticamente ───────────────────────────────
    # El usuario se llama igual que el folio del veterinario (ej: VET-001)
    # La contraseña por defecto es '12345'
    # El tipo es 'VET' y el estado inicial es 'A' (Activo)
    tipo_vet   = TipoUsuario.objects.get(codigo='VET')
    estado_act = EdoUsuario.objects.get(clave='A')
 
    Usuario.objects.create(
        usuario=veterinario.folio,          # ej: VET-001
        contrasena='12345',
        tipo=tipo_vet,
        veterinario=veterinario,
        estado=estado_act,
    )
    # ─────────────────────────────────────────────────────────────────────────
 
    return veterinario 
 
def editar_veterinario_db(veterinario, data):
    numeros = re.sub(r'\D', '', data.get('telefono', ''))
    tel_fmt = f"({numeros[:3]}) {numeros[3:6]}-{numeros[6:]}"
 
    veterinario.nombrepila      = data['nombre'].strip().title()
    veterinario.primerapellido  = data['apellido_paterno'].strip().title()
    veterinario.segundoapellido = data.get('apellido_materno', '').strip().title() or None
    veterinario.correo          = data['correo'].strip().lower()
    veterinario.telefono        = tel_fmt
    veterinario.especialidad    = Especialidad.objects.get(clave=data['especialidad'])
    veterinario.save()
    return veterinario
 
 
def dar_de_baja_veterinario(folio):
    #Cambia el estado del usuario asociado al veterinario a Inactivo
    inactivo = EdoUsuario.objects.get(clave='I')
    # Busca el usuario asociado a este veterinario
    usuario = Usuario.objects.filter(veterinario__folio=folio).first()
    if not usuario:
        return False, 'No se encontró un usuario asociado a este veterinario'
    usuario.estado = inactivo
    usuario.save()
    return True, None

#--------------------------------------------- E S P E C I A L I D A D -----------------------------------------------------------------------------------
def generar_clave_especialidad():
    #claves: SPEC-01
    claves = Especialidad.objects.values_list('clave', flat=True)
    
    max_num = 0
    for c in claves:
        try:
            num = int(c.split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue

    return f"SPEC-{max_num + 1:02d}"

def validar_datos_especialidad(data):
    nombre = data.get('nombre', '').strip()
    descripcion = data.get('descripcion', '').strip()
    
    if not nombre:
        return False, 'El nombre de la especialidad es obligatorio'
    
    #Validar nombre
    ok, msg = validar_texto(nombre, "nombre")
    if not ok:
        return False, msg
    
    if len(nombre) > 30:
        return False, 'El nombre no puede superar 30 caracteres'
    
    if not descripcion:
        return False, 'La descripción de la especialidad es obligatoria'
    
    if len(descripcion) > 100:
        return False, 'La descripción no puede superar 100 caracteres'
    
    #Validar descripción
    ok, msg = validar_texto(descripcion, "descripción")
    if not ok:
        return False, msg
    
    #Verifica que la especialidad no este registrada ya
    if Especialidad.objects.filter(nombre__iexact=nombre).exists():
        return False, f'Ya existe la especialidad "{nombre}"'
    
    return True, None

def crear_especialidad_db(data):
    
    especialidad = Especialidad.objects.create(
        clave=generar_clave_especialidad(),
        nombre=data.get('nombre').strip().title(),
        descripcion=data.get('descripcion').strip(),
    )
    return especialidad

#--------------------------------------------- P A G O S -----------------------------------------------------------------------------------
def obtener_desglose_consulta(consulta_numero):
    """
    Retorna el desglose completo para generar el pago de una consulta.
    Incluye: tarifa base de consulta, servicios extras y medicamentos.
    """
    with connection.cursor() as cursor:
 
        # Tarifa base: busca el servicio llamado 'Consulta' o similar
        cursor.execute("""
            SELECT s.clave, s.nombre, s.descripcion, s.costo, 1 as cantidad,
                   s.costo as subtotal, 'base' as tipo
            FROM servicio s
            WHERE s.nombre ILIKE '%consulta%'
            LIMIT 1
        """)
        cols = [c[0] for c in cursor.description]
        fila_base = cursor.fetchone()
        items = []
        subtotal_base = 0.0
        if fila_base:
            item = dict(zip(cols, fila_base))
            items.append(item)
            subtotal_base = float(item['costo'])
 
        # Servicios extras de la consulta
        cursor.execute("""
            SELECT s.clave, s.nombre, s.descripcion, s.costo,
                   sc.cantidad, sc.subtotal, 'servicio' as tipo
            FROM serv_cons sc
            JOIN servicio s ON sc.servicio = s.clave
            WHERE sc.consulta = %s
        """, [consulta_numero])
        cols = [c[0] for c in cursor.description]
        servicios = [dict(zip(cols, r)) for r in cursor.fetchall()]
        items.extend(servicios)
        total_servicios = sum(float(s['subtotal']) for s in servicios)
 
        # Medicamentos
        cursor.execute("""
            SELECT m.clave, m.nombre, m.descripcion, m.precio as costo,
                   t.cantidad, (t.cantidad * m.precio) as subtotal,
                   'medicamento' as tipo
            FROM tratamiento t
            JOIN medicamento m ON t.medicamento = m.clave
            JOIN receta r ON t.receta = r.numero
            WHERE r.consulta = %s
        """, [consulta_numero])
        cols = [c[0] for c in cursor.description]
        meds = [dict(zip(cols, r)) for r in cursor.fetchall()]
        items.extend(meds)
        total_meds = sum(float(m['subtotal']) for m in meds)
 
    total = round(subtotal_base + total_servicios + total_meds, 2)
    return items, total

def obtener_desglose_hospitalizacion(hosp_numero):
    """
    Desglose para pago de hospitalización.
    Dias = fechaalta - fechaingreso (mínimo 1).
    Tarifa diaria = servicio cuyo nombre contenga 'hospitaliz'.
    """
    from .models import Hospitalizacion
    hosp = Hospitalizacion.objects.select_related('expediente').get(numero=hosp_numero)
 
    dias = 1
    if hosp.fechaalta and hosp.fechaingreso:
        dias = max((hosp.fechaalta - hosp.fechaingreso).days, 1)
 
    items = []
    total_hosp = 0.0
 
    with connection.cursor() as cursor:
 
        # Tarifa diaria de hospitalización
        cursor.execute("""
            SELECT s.clave, s.nombre, s.descripcion, s.costo
            FROM servicio s
            WHERE s.nombre ILIKE '%hospitaliz%'
            LIMIT 1
        """)
        cols = [c[0] for c in cursor.description]
        fila = cursor.fetchone()
        if fila:
            srv = dict(zip(cols, fila))
            subtotal_hosp = round(float(srv['costo']) * dias, 2)
            items.append({
                'clave': srv['clave'],
                'nombre': srv['nombre'],
                'descripcion': srv['descripcion'],
                'costo': float(srv['costo']),
                'cantidad': dias,
                'subtotal': subtotal_hosp,
                'tipo': 'base',
                'nota': f'{dias} día{"s" if dias != 1 else ""} de hospitalización',
            })
            total_hosp = subtotal_hosp
 
        # Servicios extras de hospitalización
        cursor.execute("""
            SELECT s.clave, s.nombre, s.descripcion, s.costo,
                   sh.cantidad, sh.subtotal, 'servicio' as tipo
            FROM serv_hosp sh
            JOIN servicio s ON sh.servicio = s.clave
            WHERE sh.hospitalizacion = %s
        """, [hosp_numero])
        cols = [c[0] for c in cursor.description]
        servicios = [dict(zip(cols, r)) for r in cursor.fetchall()]
        items.extend(servicios)
        total_servicios = sum(float(s['subtotal']) for s in servicios)
 
        # Medicamentos
        cursor.execute("""
            SELECT m.clave, m.nombre, m.descripcion, m.precio as costo,
                   t.cantidad, (t.cantidad * m.precio) as subtotal,
                   'medicamento' as tipo
            FROM tratamiento t
            JOIN medicamento m ON t.medicamento = m.clave
            JOIN receta r ON t.receta = r.numero
            WHERE r.hospitalizacion = %s
        """, [hosp_numero])
        cols = [c[0] for c in cursor.description]
        meds = [dict(zip(cols, r)) for r in cursor.fetchall()]
        items.extend(meds)
        total_meds = sum(float(m['subtotal']) for m in meds)
 
    total = round(total_hosp + total_servicios + total_meds, 2)
    return items, total, dias

def crear_pago_db(tipo, referencia_id, total):
    """
    Crea el registro de pago.
    tipo: 'consulta' | 'hospitalizacion'
    """
    now = timezone.now()
 
    if tipo == 'consulta':
        consulta = Consulta.objects.get(numero=referencia_id)
        pago = Pago.objects.create(
            fecha=now.date(),
            hora=now.time(),
            pagofinal=total,
            consulta=consulta,
            hospitalizacion=None,
        )
        # Marcar cita como Pagada
        try:
            consulta.cita.estado = EdoCita.objects.get(nombre='Pagada')
            consulta.cita.save()
        except EdoCita.DoesNotExist:
            pass
 
    elif tipo == 'hospitalizacion':
        hosp = Hospitalizacion.objects.get(numero=referencia_id)
        consulta = hosp.consulta
        pago = Pago.objects.create(
            fecha=now.date(),
            hora=now.time(),
            pagofinal=total,
            consulta=consulta,
            hospitalizacion=hosp,
        )
        # Guardar total en la hospitalización
        hosp.total = total
        hosp.save()
 
    return pago

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
from django.core.exceptions import ObjectDoesNotExist
from .models import Usuario, EdoUsuario


def dar_baja_usuario(usuario):
    try:
        user = Usuario.objects.get(usuario=usuario)
    except Usuario.DoesNotExist:
        return False

    user.estado_id = 'I'
    user.save()
    return True