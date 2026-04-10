from .models import Propietario, Telefono, Medicamento, Servicio, Especie, Raza, Cita, Mascota, Veterinario, EdoCita, Especialidad, EdoUsuario, Usuario, Consulta, Expediente, Receta, Tratamiento
from django.utils import timezone
from datetime import date, time, datetime, timedelta
import re, json
from django.db import connection

from .utils.validaciones import (
    validar_texto,
    validar_telefono,
    validar_email,
    formatear_texto,
    limpiar_espacios
)
#--------------------------------------------- P R O P I E T A R I O S -----------------------------------------------------------------------------------

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
    tel = limpiar_espacios(data.get('tel_principal'))
    ok, msg = validar_telefono(tel)
    if not ok:
        return False, msg

    return True, None

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

    return propietario


def formatear_telefono(numero):
    if not numero:
        return None

    numeros = re.sub(r'\D', '', numero)

    if len(numeros) != 10:
        raise ValueError("El teléfono debe tener 10 dígitos")

    return f"({numeros[:3]}) {numeros[3:6]}-{numeros[6:]}"

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
def validar_datos_consulta(data):
    sintomas    = data.get('sintomas', '').strip()
    diagnostico = data.get('diagnostico', '').strip()
    observaciones = data.get('observaciones', '').strip()

    try:
        temp = float(data.get('temperatura', 0))
        fc   = int(data.get('freccardiaca', 0))
        fr   = int(data.get('frecrespiratoria', 0))
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
    if temp <= 0:
        return False, 'La temperatura es obligatoria'
    if fc <= 0:
        return False, 'La frecuencia cardíaca es obligatoria'
    if fr <= 0:
        return False, 'La frecuencia respiratoria es obligatoria'
 
    return True, None

def guardar_consulta_db(cita, data):
    """
    Crea Expediente (si no existe), Consulta, actualiza estado de cita,
    y opcionalmente crea Receta + Tratamientos.
    """
    # 1. Expediente — crear si la mascota no tiene uno
    expediente, _ = Expediente.objects.get_or_create(
        mascota=cita.mascota,
        defaults={'fechaapertura': timezone.now().date()}
    )
    
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
    
    # 4. Receta + Tratamientos (si se agregaron medicamentos)
    medicamentos_json = data.get('medicamentos_json', '[]')
    try:
        medicamentos_list = json.loads(medicamentos_json)
    except (json.JSONDecodeError, TypeError):
        medicamentos_list = []
 
    if medicamentos_list:
        instrugenerales = data.get('instrugenerales', '').strip()
        receta = Receta.objects.create(
            fecha=timezone.now().date(),
            instrugenerales=instrugenerales or 'Ver indicaciones por medicamento',
            consulta=consulta,
        )
        
        # Insertar tratamientos con SQL pa evitar el id
        with connection.cursor() as cursor:
            for item in medicamentos_list:
                cursor.execute("""
                    INSERT INTO tratamiento
                    (receta, medicamento, cantidad, dosis, frecuencia, duracion, notas)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    receta.numero,
                    item['clave'],
                    int(item.get('cantidad', 1)),
                    item.get('dosis', ''),
                    item.get('frecuencia', ''),
                    item.get('duracion', ''),
                    item.get('notas', ''),    
                ])
        
    return consulta

def actualizar_consulta_db(consulta, data):
    """Edita sintomas, diagnostico y observaciones de una consulta existente."""
    consulta.sintomas     = data['sintomas'].strip()
    consulta.diagnostico  = data['diagnostico'].strip()
    consulta.observaciones = data['observaciones'].strip()
    consulta.save()
    return consulta

#--------------------------------------------- M E D I C A M E N T O S -----------------------------------------------------------------------------------
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

def crear_veterinario_db(data):
    numeros   = re.sub(r'\D', '', data.get('telefono', ''))
    tel_fmt   = f"({numeros[:3]}) {numeros[3:6]}-{numeros[6:]}"
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