from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import plotly.graph_objects as go

USER_ID = 'user1'


def progressao_turma(request):
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')

    df_historico = pd.read_csv(historico_path)
    df_alunos = pd.read_csv(alunos_path)

    df_historico['PERIODO_NUM'] = df_historico['PERIODO'].str.extract(r'(\d)')[
        0].astype(float)
    df_historico = df_historico.sort_values(
        ['MATR ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_NUM'])
    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    df_historico['ANO_PERIODO'] = df_historico['ANO'].astype(
        str) + ' - ' + df_historico['PERIODO']

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
        return render(request, 'progressao_turma.html', {
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
        return render(request, 'progressao_turma.html', {
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

    linhas = []  # Cria uma lista para armazenar as linhas do gráfico
    # Percorre os status de reprovação e armazena cada parte do par em uma variável
    for status, cor in status_reprovados.items():
        # Filtra os dados do aluno para cada status
        dados_status = dados_aluno[dados_aluno['STATUS'] == status]
        if dados_status.empty:
            continue
        # Y é o valor da soma das cargas horárias agrupadas por período, garantindo que todos os períodos estejam presentes.
        y = dados_status.groupby('ANO_PERIODO')[
            'CARGA'].sum().reindex(periodos, fill_value=0)
        hover = (  # Cria o texto de hover para cada ponto, combinando nome da disciplina e status
            dados_status.assign(
                # Cria uma nova coluna texto que combina nome da disciplina + status
                texto=lambda df: df['DISCIPLINA'] +
                "<br>Status: " + df['STATUS']
            )
            .groupby('ANO_PERIODO')['texto']
            .apply("<br>".join)  # Agrupa e quebra linha
            .reindex(periodos, fill_value="Nenhuma disciplina")
            .tolist()
        )
        linha = go.Scatter(  # Não existe nada como "go.Lines", o padrão é go.Scatter com mode='lines'
            x=periodos,
            y=y,
            mode='lines+markers',  # Mantenha a linha com marcadores
            name=status,
            line=dict(color=cor),  # Cor da linha
            hoverinfo='text',
            hovertext=hover
            )
        linhas.append(linha)  # Adiciona a linha à lista de linhas do gráfico

    # Cria uma cópia da carga acumulada para usar como base das barras
    base_aprovada = carga_aprovada_acumulada.copy()
    for status, cor in status_aprovados.items():  # Loop no status de aprovação
        dados_status = dados_aluno[dados_aluno['STATUS'] == status]
        if dados_status.empty:
            continue
        y = dados_status.groupby('ANO_PERIODO')[
            'CARGA'].sum().reindex(periodos, fill_value=0)
        hover = (
            dados_status
            .assign(
                # Cria uma nova coluna texto que combina nome da disciplina + status
                texto=lambda df: df['DISCIPLINA'] +
                "<br>Status: " + df['STATUS']
            )
            .groupby('ANO_PERIODO')['texto']
            .apply("<br>".join)  # Agrupa e quebra linha
            .reindex(periodos, fill_value="Nenhuma disciplina")
            .tolist()
        )
        linha = go.Scatter(  # Não existe nada como "go.Lines", o padrão é go.Scatter com mode='lines'
            x=periodos,
            y=y,
            mode='lines+markers',  # Mantenha a linha com marcadores
            name=status,
            line=dict(color=cor),  # Cor da linha
            hoverinfo='text',
            hovertext=hover
            )
        linhas.append(linha)

    if not linhas:
        alunos_options = [
            {'id': str(matr_aluno),
             'label': f"{matr_aluno} - {nome_pessoa}"}
            for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
        ]
        mensagem = "Não há dados disponíveis para a turma selecionada."
        return render(request, 'progressao_turma.html', {
            'plot_div': '',
            'alunos_options': alunos_options,
            'selected_id': str(matr_aluno),
            'mensagem': mensagem,
        })

    carga_referencia = 3240
    linha_referencia = go.Scatter(  # Cria uma linha de referência para a carga horária total
        x=periodos,
        y=[carga_referencia] * len(periodos),
        mode='lines',
        name='C.H. Total',
        line=dict(color='rgba(100,100,100,0.3)')
    )
    linhas.append(linha_referencia)

    # Cria a figura usando as linhas criadas anteriormente
    fig = go.Figure(linhas)
    fig.update_layout(  # Configurações de layout do gráfico
        font=dict(size=18),
        xaxis_title='Ano - Período',
        yaxis_title='Carga Horária',
        xaxis=dict(tickfont=dict(size=16)),
        yaxis=dict(tickfont=dict(size=16)),
        height=800,
        width=1800
    )

    alunos_options = [  # Cria as opções de alunos para o dropdown
        {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
        for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
    ]

    # Converte a figura para HTML para ser renderizada na template
    plot_div = fig.to_html(full_html=False)
    return render(request, 'progressao_turma.html', {
        'plot_div': plot_div,
        'alunos_options': alunos_options,
        'selected_id': str(matr_aluno),
    })
