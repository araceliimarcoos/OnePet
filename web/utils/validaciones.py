import re

# VALIDAR TEXTO - SOLO LETRAS
def validar_texto(texto, campo="texto"):
    if not texto:
        return False, f"El {campo} es obligatorio"

    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', texto):
        return False, f"El {campo} solo debe contener letras"

    return True, None

    return True, None
# MAYUSCULA AL INICIO
def formatear_texto(texto):
    return texto.strip().title()

# QUITAR ESPACIOS (TELEFONO)
def limpiar_espacios(texto):
    return re.sub(r'\D', '', texto) if texto else ''

# VALIDAR TELEFONO - SOLO NUMEROS
def validar_telefono(telefono):
    if not telefono:
        return False, "El teléfono es obligatorio"
    
    solo_numeros = re.sub(r'\D', '', telefono)
    
    if not solo_numeros:
        return False, "El teléfono debe es obligatorio"

    if len(solo_numeros) != 10:
        return False, "El teléfono debe tener exactamente 10 dígitos"
    
    return True, None

# VALIDAR EMAIL
def validar_email(email):
    if not email:
        return False, "El correo es obligatorio"

    email = email.strip().lower()

    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    if not re.match(patron, email):
        return False, "El formato del correo no es válido"

    return True, None


