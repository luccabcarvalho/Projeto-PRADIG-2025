from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
import os
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go

USER_ID = 'user1'



def desempenho_aluno_periodo(request):
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')

    df_historico = pd.read_csv(historico_path)
    df_alunos = pd.read_csv(alunos_path)

    df_historico['PERIODO_NUM'] = df_historico['PERIODO'].str.extract(r'(\d)')[0].astype(float)
    df_historico = df_historico.sort_values(['MATR ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_NUM'])
    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    df_historico['ANO_PERIODO'] = df_historico['ANO'].astype(str) + ' - ' + df_historico['PERIODO']

    matr_aluno_param = request.GET.get('matr_aluno')
    if matr_aluno_param:
        try:
            matr_aluno = int(matr_aluno_param)
            if matr_aluno not in df_historico['MATR ALUNO'].values:
                matr_aluno = df_historico['MATR ALUNO'].iloc[0]
        except (ValueError, TypeError):
            matr_aluno = df_historico['MATR ALUNO'].iloc[0]
    else:
        matr_aluno = df_historico['MATR ALUNO'].iloc[0]

    dados_aluno = df_historico[df_historico['MATR ALUNO'] == matr_aluno].copy()
    if dados_aluno.empty:
        alunos_options = [
            {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
            for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
        ]
        mensagem = "Não há dados disponíveis para o aluno selecionado."
        return render(request, 'desempenho_aluno_periodo.html', {
            'plot_div': '',
            'alunos_options': alunos_options,
            'selected_id': str(matr_aluno),
            'mensagem': mensagem,
        })

    dados_aluno['STATUS'] = dados_aluno['DESCR SITUACAO'].str.strip()
    dados_aluno['CARGA'] = dados_aluno['TOTAL CARGA HORARIA']
    dados_aluno['DISCIPLINA'] = (
        dados_aluno['COD ATIV CURRIC'].astype(str) + ' - ' +
        dados_aluno['NOME ATIV CURRIC'] + ' (' +
        dados_aluno['CARGA'].astype(str) + 'h)'
    )

    def ordenar_periodo(periodo):
        ano, per = periodo.split(' - ')
        return int(ano) * 10 + (1 if '1' in per else 2)

    periodos = sorted(dados_aluno['ANO_PERIODO'].unique(), key=ordenar_periodo)
    if not periodos:
        alunos_options = [
            {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
            for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
        ]
        mensagem = "Não há dados disponíveis para o aluno selecionado."
        return render(request, 'desempenho_aluno_periodo.html', {
            'plot_div': '',
            'alunos_options': alunos_options,
            'selected_id': str(matr_aluno),
            'mensagem': mensagem,
        })

    status_aprovados = {
        'APV - Aprovado': '#006400',
        'APV- Aprovado': '#006400',
        'APV - Aprovado sem nota': '#32CD32',
        'ADI - Aproveitamento': '#7CFC00',
        'ADI - Aproveitamento de créditos da disciplina': '#ADFF2F',
        'ADI - Dispensa com nota': '#228B22',
        'DIS - Dispensa sem nota': '#32CD32',
    }
    status_reprovados = {
        'REP - Reprovado por nota/conceito': '#8B0000',
        'REF - Reprovado por falta': '#CD5C5C',
        'ASC - Reprovado sem nota': '#FFA07A',
        'TRA - Trancamento de disciplina': '#8B0000',
    }
    cores_status = {**status_aprovados, **status_reprovados}

    carga_aprovada_acumulada = (
        dados_aluno[dados_aluno['STATUS'].isin(status_aprovados.keys())]
        .groupby('ANO_PERIODO')['CARGA']
        .sum()
        .reindex(periodos, fill_value=0)
        .cumsum()
        .shift(fill_value=0)
    )

    barras = []
    for status, cor in status_reprovados.items():
        dados_status = dados_aluno[dados_aluno['STATUS'] == status]
        if dados_status.empty:
            continue
        y = dados_status.groupby('ANO_PERIODO')['CARGA'].sum().reindex(periodos, fill_value=0)
        hover = dados_status.groupby('ANO_PERIODO').apply(
            lambda grupo: "<br>".join(
                f"{linha['DISCIPLINA']}<br>Status: {linha['STATUS']}" for _, linha in grupo.iterrows()
            )
        ).reindex(periodos, fill_value="Nenhuma disciplina").tolist()
        barra = go.Bar(
            x=periodos,
            y=y,
            base=(carga_aprovada_acumulada - y).tolist(),
            name=status,
            marker_color=cor,
            hoverinfo='text',
            hovertext=hover
        )
        barras.append(barra)

    base_aprovada = carga_aprovada_acumulada.copy()
    for status, cor in status_aprovados.items():
        dados_status = dados_aluno[dados_aluno['STATUS'] == status]
        if dados_status.empty:
            continue
        y = dados_status.groupby('ANO_PERIODO')['CARGA'].sum().reindex(periodos, fill_value=0)
        hover = dados_status.groupby('ANO_PERIODO').apply(
            lambda grupo: "<br>".join(
                f"{linha['DISCIPLINA']}<br>Status: {linha['STATUS']}" for _, linha in grupo.iterrows()
            )
        ).reindex(periodos, fill_value="Nenhuma disciplina").tolist()
        barra = go.Bar(
            x=periodos,
            y=y,
            base=base_aprovada.tolist(),
            name=status,
            marker_color=cor,
            hoverinfo='text',
            hovertext=hover
        )
        barras.append(barra)
        base_aprovada += y

    if not barras:
        alunos_options = [
            {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
            for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
        ]
        mensagem = "Não há dados disponíveis para o aluno selecionado."
        return render(request, 'desempenho_aluno_periodo.html', {
            'plot_div': '',
            'alunos_options': alunos_options,
            'selected_id': str(matr_aluno),
            'mensagem': mensagem,
        })

    carga_referencia = 3240
    linha_referencia = go.Scatter(
        x=periodos,
        y=[carga_referencia] * len(periodos),
        mode='lines',
        name='C.H. Total',
        line=dict(color='rgba(100,100,100,0.3)')
    )
    barras.append(linha_referencia)

    fig = go.Figure(barras)
    fig.update_layout(
        font=dict(size=18),
        barmode='stack',
        xaxis_title='Ano - Período',
        yaxis_title='Carga Horária',
        xaxis=dict(tickfont=dict(size=16)),
        yaxis=dict(tickfont=dict(size=16)),
        height=800,
        width=1800
    )

    alunos_options = [
        {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
        for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
    ]

    plot_div = fig.to_html(full_html=False)
    return render(request, 'desempenho_aluno_periodo.html', {
        'plot_div': plot_div,
        'alunos_options': alunos_options,
        'selected_id': str(matr_aluno), 
    })

def home(request):
    return render(request, 'home.html')

# Upload de arquivos

USER_ID = 'user1'
USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)

CURRICULOS_DIR = os.path.join(settings.MEDIA_ROOT, 'curriculos_bsi')

def ensure_user_dirs():
    os.makedirs(USER_DIR, exist_ok=True)
    os.makedirs(CURRICULOS_DIR, exist_ok=True)

def checar_arquivos_necessarios(request):
    """
    Recebe via GET o parâmetro 'visualizacao' e retorna JSON com arquivos faltantes.
    """
    visualizacao = request.GET.get('visualizacao')
    USER_ID = 'user1' 
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    CURRICULOS_DIR = os.path.join(settings.MEDIA_ROOT, 'curriculos_bsi')
    faltando = []
    if visualizacao == 'desempenho_aluno_periodo':
        if not os.path.exists(os.path.join(USER_DIR, 'alunosPorCurso.csv')):
            faltando.append('alunosPorCurso.csv')
        if not os.path.exists(os.path.join(USER_DIR, 'historicoEscolar.csv')):
            faltando.append('historicoEscolar.csv')
    elif visualizacao == 'status_integralizacao':
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

def gerenciar_arquivos(request):
    ensure_user_dirs()
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')
    curriculos = []
    curriculos_padrao = [
        'curriculo-20002.csv',
        'curriculo-20052.csv',
        'curriculo-20081.csv',
        'curriculo-20232.csv',
    ]
    if os.path.exists(CURRICULOS_DIR):
        curriculos = [c for c in curriculos_padrao if os.path.exists(os.path.join(CURRICULOS_DIR, c))]
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        if tipo in ['alunos', 'historico']:
            f = request.FILES.get('arquivo')
            if f:
                filename = 'alunosPorCurso.csv' if tipo == 'alunos' else 'historicoEscolar.csv'
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
            elif arquivo in curriculos_padrao:
                os.remove(os.path.join(CURRICULOS_DIR, arquivo))
            messages.success(request, f'Arquivo removido com sucesso!')
            return redirect('gerenciar_arquivos')
    context = {
        'alunos': os.path.exists(alunos_path),
        'historico': os.path.exists(historico_path),
        'curriculos': [c for c in curriculos_padrao if os.path.exists(os.path.join(CURRICULOS_DIR, c))],
    }
    return render(request, 'gerenciar_arquivos.html', context)