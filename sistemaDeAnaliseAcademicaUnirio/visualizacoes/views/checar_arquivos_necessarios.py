from django.http import JsonResponse
from django.conf import settings
import os

USER_ID = 'user1'
USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)

CURRICULOS_DIR = os.path.join(settings.MEDIA_ROOT, 'curriculos_bsi')

def checar_arquivos_necessarios(request):
    """
    Recebe via GET o parâmetro 'visualizacao' e retorna JSON com arquivos faltantes.
    """
    visualizacao = request.GET.get('visualizacao')
    USER_ID = 'user1' 
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    CURRICULOS_DIR = os.path.join(settings.MEDIA_ROOT, 'curriculos_bsi')
    faltando = []
    if visualizacao == 'progressao_individual':
        if not os.path.exists(os.path.join(USER_DIR, 'alunosPorCurso.csv')):
            faltando.append('alunosPorCurso.csv')
        if not os.path.exists(os.path.join(USER_DIR, 'historicoEscolar.csv')):
            faltando.append('historicoEscolar.csv')
    elif visualizacao == 'prazos_de_integralizacao':
        if not os.path.exists(os.path.join(USER_DIR, 'alunosPorCurso.csv')):
            faltando.append('alunosPorCurso.csv')
        if not os.path.exists(os.path.join(USER_DIR, 'historicoEscolar.csv')):
            faltando.append('historicoEscolar.csv')
    elif visualizacao == 'matriz_de_progressao':
        if not os.path.exists(os.path.join(USER_DIR, 'alunosPorCurso.csv')):
            faltando.append('alunosPorCurso.csv')
        if not os.path.exists(os.path.join(USER_DIR, 'historicoEscolar.csv')):
            faltando.append('historicoEscolar.csv')
        if not os.path.exists(os.path.join(CURRICULOS_DIR, 'curriculos-bsi.csv')):
            faltando.append('curriculos-bsi.csv')
    return JsonResponse({'faltando': faltando})