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
        curriculos = [
            'curriculo-20002.csv',
            'curriculo-20052.csv',
            'curriculo-20081.csv',
            'curriculo-20232.csv',
        ]
        curriculos_faltando = [c for c in curriculos if not os.path.exists(os.path.join(CURRICULOS_DIR, c))]
        faltando.extend(curriculos_faltando)
    return JsonResponse({'faltando': faltando})