import pandas as pd
import numpy as np
import plotly.graph_objects as go
from django.shortcuts import render
import os

def status_integralizacao(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, 'visualizacoes', 'data')
    df_alunos = pd.read_csv(os.path.join(data_dir, 'alunosPorCurso.csv'))
    df_hist = pd.read_csv(os.path.join(data_dir, 'HistoricoEscolarSimplificado.csv'))

    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    alunos = df_hist['MATR ALUNO'].unique().tolist()

    blocos = [
        ('Prazo Previsto', 8, '#6fa8dc'),
        ('Prazo Máximo', 2, '#9fc5e8'),
        ('Exigir plano de integralização', 2, '#f6b26b'),
        ('Prorrogação Máxima', 2, '#f9cb9c'),
        ('Situação Irregular', 2, '#e06666'),
    ]

    status_aprovados = {
        'APV - Aprovado', 'APV- Aprovado', 'APV - Aprovado sem nota',
        'ADI - Aproveitamento', 'ADI - Aproveitamento de créditos da disciplina',
        'ADI - Dispensa com nota', 'DIS - Dispensa sem nota'
    }
    status_reprovados = {
        'REP - Reprovado por nota/conceito', 'REF - Reprovado por falta',
        'ASC - Reprovado sem nota', 'TRA - Trancamento de disciplina'
    }
    status_matriculado = {'ASC - Matrícula'}

    colunas = []
    cores = []
    for nome, tam, cor in blocos:
        colunas += [nome] + [""] * (tam - 1)
        cores += [cor] * tam
    n_periodos = len(colunas)

    df_hist['PERIODO_LABEL'] = (
        df_hist['ANO'].astype(str).str[-2:] + '/' +
        df_hist['PERIODO'].astype(str).str.replace('. semestre', '', regex=False).str.strip()
    )

    mapa_matricula_nome = dict(zip(df_hist['MATR ALUNO'], df_hist['NOME PESSOA']))

    aluno_periodos = {}
    for matricula, grupo in df_hist.groupby('MATR ALUNO'):
        periodos = grupo['PERIODO_LABEL'].drop_duplicates().tolist()
        aluno_periodos[matricula] = periodos

    def tooltip_periodo(matricula, periodo):
        aluno_nome = mapa_matricula_nome.get(matricula, str(matricula))
        dados = df_hist[(df_hist['MATR ALUNO'] == matricula) & (df_hist['PERIODO_LABEL'] == periodo)]
        if dados.empty:
            return periodo

        aprovadas = []
        reprovadas = []
        matriculadas = []
        outros = []
        for _, row in dados.iterrows():
            status = str(row['DESCR SITUACAO']).strip()
            disciplina = f"{row['COD ATIV CURRIC']} - {row['NOME ATIV CURRIC']} ({row['TOTAL CARGA HORARIA']}h)"
            if status in status_aprovados:
                aprovadas.append(disciplina)
            elif status in status_reprovados:
                reprovadas.append(disciplina)
            elif status in status_matriculado:
                matriculadas.append(disciplina)
            else:
                outros.append(f"{disciplina} [{status}]")

        tooltip = f"<b>Aluno:</b> {aluno_nome}<br><b>Período:</b> {periodo}<br>"
        if aprovadas:
            tooltip += "<b>Aprovadas:</b><br>" + "<br>".join(aprovadas) + "<br>"
        if reprovadas:
            tooltip += "<b>Reprovadas:</b><br>" + "<br>".join(reprovadas) + "<br>"
        if matriculadas:
            tooltip += "<b>Matriculadas:</b><br>" + "<br>".join(matriculadas) + "<br>"
        if outros:
            tooltip += "<b>Outros:</b><br>" + "<br>".join(outros) + "<br>"
        return tooltip

    matriz = []
    tooltip_matriz = []
    for matricula in alunos:
        periodos = aluno_periodos.get(matricula, [])
        linha = [''] * n_periodos
        tooltips = [''] * n_periodos
        limite = min(len(periodos), n_periodos)
        for i in range(limite):
            linha[i] = periodos[i]
            tooltips[i] = tooltip_periodo(matricula, periodos[i])
        if len(periodos) > n_periodos:
            linha[-1] = '+'
            excedentes = periodos[n_periodos - 1:]
            tooltips[-1] = 'Períodos excedentes: ' + ', '.join(excedentes)
        matriz.append(linha)
        tooltip_matriz.append(tooltips)

    fig = go.Figure(data=go.Heatmap(
        z=[[i for i in range(n_periodos)] for _ in range(len(alunos))],
        x=[f'{colunas[i]} {i+1}' for i in range(n_periodos)],
        y=[f"{matricula} - {mapa_matricula_nome.get(matricula, '')}" for matricula in alunos],
        text=matriz,
        customdata=tooltip_matriz,
        hovertemplate='%{customdata}',
        texttemplate='%{text}',
        colorscale=[[i/(n_periodos-1), cor] for i, cor in enumerate(cores)],
        showscale=False
    ))

    for i, cor in enumerate(cores):
        fig.add_shape(
            type="rect",
            x0=i-0.5, x1=i+0.5,
            y0=-0.5, y1=len(alunos)-0.5,
            fillcolor=cor, line=dict(width=0),
            layer="below"
        )

    fig.update_traces(
        showscale=False,
        textfont=dict(size=13, color='black'),
    )

    fig.update_layout(
        title='Status de Integralização dos Alunos por Período',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(n_periodos)),
            ticktext=[f'{colunas[i]}' for i in range(n_periodos)],
            tickangle=45,
            side='top',
            range=[-0.5, 25.5]
        ),
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=12),
            scaleanchor="x",
            scaleratio=1,
            range=[-0.5, 14.5]
        ),
        autosize=False,
        width=1800,
        height=900,
        margin=dict(l=10, r=10, t=80, b=10),
    )

    plot_div = fig.to_html(full_html=False)
    return render(request, 'status_integralizacao.html', {'plot_div': plot_div})