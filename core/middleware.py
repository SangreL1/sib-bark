"""
Middleware de Ciberseguridad — SIB Bark
Previene que el navegador cachee páginas privadas.
Si el usuario cierra sesión y presiona "Atrás", el servidor verá
la sesión inválida y redirigirá al login en vez de mostrar datos cacheados.
"""


class NoCacheMiddleware:
    """
    Agrega encabezados HTTP anti-caché a todas las respuestas.
    Esto garantiza que el botón "Atrás" del navegador siempre
    valide la sesión con el servidor, bloqueando el acceso a
    páginas privadas tras el cierre de sesión.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Solo inyectar en páginas que no sean estáticas/media
        path = request.path
        if not (path.startswith('/static/') or path.startswith('/media/')):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response
