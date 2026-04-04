from .models import Propietario, Telefono
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