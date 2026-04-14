from .models import Usuario

class UsuarioBackend:
    def authenticate(self, request, username=None, password=None):
        try:
            user = Usuario.objects.get(usuario=username)
            if user.contrasena == password:
                # EL PARCHE DEFINITIVO:
                # Sobrescribimos el método save en memoria para este objeto.
                # Cuando Django intente guardar el last_login, llamará a esta 
                # función que no hace nada y no dará error.
                user.save = lambda *args, **kwargs: None
                
                user._backend = 'web.backend.UsuarioBackend'
                return user
        except Usuario.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            user = Usuario.objects.get(pk=user_id)
            # También lo aplicamos aquí por seguridad
            user.save = lambda *args, **kwargs: None
            return user
        except Usuario.DoesNotExist:
            return None