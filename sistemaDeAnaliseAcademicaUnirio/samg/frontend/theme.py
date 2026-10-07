"""
Gerenciador de tema (claro/escuro) para SAMG
"""
from django.http import HttpResponseRedirect
from django.urls import reverse


THEME_CHOICES = ('light', 'dark')
DEFAULT_THEME = 'light'
THEME_SESSION_KEY = 'theme'


def get_user_theme(request):
    """Obtém o tema preferido do usuário da sessão"""
    return request.session.get(THEME_SESSION_KEY, DEFAULT_THEME)


def set_user_theme(request, theme):
    """Salva o tema preferido do usuário na sessão"""
    if theme in THEME_CHOICES:
        request.session[THEME_SESSION_KEY] = theme
        request.session.modified = True


def toggle_theme(request):
    """View que alterna entre os temas"""
    current_theme = get_user_theme(request)
    new_theme = 'dark' if current_theme == 'light' else 'light'
    set_user_theme(request, new_theme)
    
    # Redirecionar para a página anterior
    next_url = request.META.get('HTTP_REFERER', '/')
    return HttpResponseRedirect(next_url)


def theme_context(request):
    """Context processor que adiciona o tema ao contexto"""
    return {
        'user_theme': get_user_theme(request),
        'toggle_theme_url': reverse('toggle_theme')
    }

