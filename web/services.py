from .models import Propietario, Telefono, Medicamento, Servicio
import re

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