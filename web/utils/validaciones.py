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
    return texto.replace(" ", "")

# VALIDAR TELEFONO - SOLO NUMEROS
def validar_telefono(telefono):
    if not telefono:
        return False, "El teléfono es obligatorio"

    if not re.match(r'^[0-9\s]+$', telefono):
        return False, "El teléfono solo debe contener números"
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


