from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
import os

USER_ID = 'user1'
USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
CURRICULOS_DIR = os.path.join(settings.MEDIA_ROOT, 'curriculos_bsi')


def ensure_user_dirs():
    os.makedirs(USER_DIR, exist_ok=True)
    os.makedirs(CURRICULOS_DIR, exist_ok=True)


def gerenciar_arquivos(request):
    ensure_user_dirs()

    alunos_path       = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path    = os.path.join(USER_DIR, 'historicoEscolar.csv')
    equivalencias_path = os.path.join(USER_DIR, 'relacaoEquivalenciaDisciplinas.csv')  # ← novo

    curriculos_padrao = [
        'curriculo-20002.csv',
        'curriculo-20052.csv',
        'curriculo-20081.csv',
        'curriculo-20232.csv',
    ]

    if request.method == 'POST':
        tipo = request.POST.get('tipo')

        if tipo in ['alunos', 'historico', 'equivalencias']:  # ← adicionado 'equivalencias'
            f = request.FILES.get('arquivo')
            if f:
                filename_map = {
                    'alunos':       'alunosPorCurso.csv',
                    'historico':    'historicoEscolar.csv',
                    'equivalencias': 'relacaoEquivalenciaDisciplinas.csv',  # ← novo
                }
                filename = filename_map[tipo]
                with open(os.path.join(USER_DIR, filename), 'wb+') as dest:
                    for chunk in f.chunks():
                        dest.write(chunk)
                messages.success(request, f'Arquivo {filename} enviado com sucesso!')
                return redirect('gerenciar_arquivos')

        elif tipo == 'curriculo':
            f = request.FILES.get('arquivo')
            if f:
                curriculos_existentes = [c for c in curriculos_padrao if os.path.exists(os.path.join(CURRICULOS_DIR, c))]
                if len(curriculos_existentes) >= 4:
                    messages.error(request, 'Limite de 4 currículos atingido. Remova um currículo antes de enviar outro.')
                    return redirect('gerenciar_arquivos')
                for curriculo_nome in curriculos_padrao:
                    curriculo_path = os.path.join(CURRICULOS_DIR, curriculo_nome)
                    if not os.path.exists(curriculo_path):
                        with open(curriculo_path, 'wb+') as dest:
                            for chunk in f.chunks():
                                dest.write(chunk)
                        messages.success(request, f'Currículo enviado como {curriculo_nome}!')
                        break
                return redirect('gerenciar_arquivos')

        elif 'remover' in request.POST:
            arquivo = request.POST.get('remover')
            if arquivo == 'alunosPorCurso.csv':
                os.remove(alunos_path)
            elif arquivo == 'historicoEscolar.csv':
                os.remove(historico_path)
            elif arquivo == 'relacaoEquivalenciaDisciplinas.csv':  # ← novo
                os.remove(equivalencias_path)
            elif arquivo in curriculos_padrao:
                os.remove(os.path.join(CURRICULOS_DIR, arquivo))
            messages.success(request, 'Arquivo removido com sucesso!')
            return redirect('gerenciar_arquivos')

    context = {
        'alunos':        os.path.exists(alunos_path),
        'historico':     os.path.exists(historico_path),
        'equivalencias': os.path.exists(equivalencias_path),  # ← novo
        'curriculos':    [c for c in curriculos_padrao if os.path.exists(os.path.join(CURRICULOS_DIR, c))],
    }
    return render(request, 'gerenciar_arquivos.html', context)