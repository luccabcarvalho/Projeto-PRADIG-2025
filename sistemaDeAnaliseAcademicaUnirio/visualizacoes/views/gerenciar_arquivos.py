from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
import os

USER_ID = 'user1'
USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)


def ensure_user_dirs():
    os.makedirs(USER_DIR, exist_ok=True)


def gerenciar_arquivos(request):
    ensure_user_dirs()

    alunos_path        = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path     = os.path.join(USER_DIR, 'historicoEscolar.csv')
    equivalencias_path = os.path.join(USER_DIR, 'relacaoEquivalenciaDisciplinas.csv')
    curriculos_path    = os.path.join(USER_DIR, 'curriculos-bsi.csv')

    if request.method == 'POST':
        tipo = request.POST.get('tipo')

        if tipo in ['alunos', 'historico', 'equivalencias', 'curriculo']:
            f = request.FILES.get('arquivo')
            if f:
                filename_map = {
                    'alunos':        'alunosPorCurso.csv',
                    'historico':     'historicoEscolar.csv',
                    'equivalencias': 'relacaoEquivalenciaDisciplinas.csv',
                    'curriculo':     'curriculos-bsi.csv',
                }
                filename = filename_map[tipo]
                with open(os.path.join(USER_DIR, filename), 'wb+') as dest:
                    for chunk in f.chunks():
                        dest.write(chunk)
                messages.success(request, f'Arquivo {filename} enviado com sucesso!')
                return redirect('gerenciar_arquivos')

        elif 'remover' in request.POST:
            arquivo = request.POST.get('remover')
            if arquivo == 'alunosPorCurso.csv':
                os.remove(alunos_path)
            elif arquivo == 'historicoEscolar.csv':
                os.remove(historico_path)
            elif arquivo == 'relacaoEquivalenciaDisciplinas.csv':
                os.remove(equivalencias_path)
            elif arquivo == 'curriculos-bsi.csv':
                os.remove(curriculos_path)
            messages.success(request, 'Arquivo removido com sucesso!')
            return redirect('gerenciar_arquivos')

    context = {
        'alunos':        os.path.exists(alunos_path),
        'historico':     os.path.exists(historico_path),
        'equivalencias': os.path.exists(equivalencias_path),
        'curriculos':    os.path.exists(curriculos_path),
    }
    return render(request, 'gerenciar_arquivos.html', context)