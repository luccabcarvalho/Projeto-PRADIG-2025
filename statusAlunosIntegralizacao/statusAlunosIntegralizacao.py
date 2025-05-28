import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc

# Leitura dos dados
df_alunos = pd.read_csv(r'docs/alunosPorCurso.csv')
df_hist = pd.read_csv(r'docs/HistoricoEscolarSimplificado.csv')

df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
alunos = df_alunos['NOME PESSOA'].tolist()

# Definição dos blocos de períodos (igual à imagem)
blocos = [
    ('Prazo Previsto', 8, '#6fa8dc'),
    ('Prazo Máximo', 2, '#9fc5e8'),
    ('Exigir plano de integralização', 2, '#f6b26b'),
    ('Prorrogação Máxima', 2, '#f9cb9c'),
    ('Situação Irregular', 2, '#e06666'),
    ('Mobilidade', 1, '#93c47d'),
    ('Períodos Excepcionais', 3, '#ffe599'),
    ('Atividades Calendário Emergencial', 2, '#ffd966'),
    ('Trancamentos Totais (regulares)', 2, '#b7b7b7'),
    ('Trancamentos Totais (especiais)', 2, '#cccccc'),
]
colunas = []
cores = []
for nome, tam, cor in blocos:
    colunas += [nome] * tam
    cores += [cor] * tam
n_periodos = len(colunas)

# Para cada aluno, obter todos os períodos cursados (ex: '19/2º', '20/1º', ...)
df_hist['PERIODO_LABEL'] = (
    df_hist['ANO'].astype(str).str[-2:] + '/' +
    df_hist['PERIODO'].astype(str).str.replace('. semestre', '', regex=False).str.strip()
)
aluno_periodos = {aluno: [] for aluno in alunos}
mapa_nome_id = dict(zip(df_alunos['NOME PESSOA'], df_alunos['ID PESSOA']))

for _, row in df_hist.iterrows():
    nome = df_alunos.loc[df_alunos['ID PESSOA'] == row['ID PESSOA'], 'NOME PESSOA']
    if not nome.empty:
        aluno = nome.values[0]
        periodo = row['PERIODO_LABEL']
        if periodo not in aluno_periodos[aluno]:
            aluno_periodos[aluno].append(periodo)

# Preencher matriz: cada célula recebe o período cursado (ou vazio)
matriz = []
for aluno in alunos:
    periodos = aluno_periodos[aluno]
    linha = []
    for i in range(n_periodos):
        if i < len(periodos):
            linha.append(periodos[i])
        else:
            linha.append('')
    matriz.append(linha)

# Geração do heatmap
fig = go.Figure(data=go.Heatmap(
    z=[[i for i in range(n_periodos)] for _ in range(len(alunos))],  
    x=[f'{colunas[i]} {i+1}' for i in range(n_periodos)],
    y=alunos,
    text=matriz,
    hoverinfo='text',
    texttemplate='%{text}',
    colorscale=[ [i/(n_periodos-1), cor] for i, cor in enumerate(cores) ],
    showscale=False
))

# Ajuste visual para células quadradas e cores de fundo por bloco
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
    hovertemplate='%{text}',
)

fig.update_layout(
    title='Status de Integralização dos Alunos por Período',
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(n_periodos)),
        ticktext=[f'{colunas[i]}' for i in range(n_periodos)],
        tickangle=45,
        side='top'
    ),
    yaxis=dict(
        automargin=True,
        tickfont=dict(size=12),
        scaleanchor="x",
        scaleratio=1
    ),
    autosize=False,
    width=1800,
    height=900,
    margin=dict(l=10, r=10, t=80, b=10),
)

# Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H2("Status de Integralização dos Alunos por Período"),
    dcc.Graph(figure=fig, style={'width': '300vw', 'height': '90vh', 'overflowY': 'scroll'})
])

if __name__ == '__main__':
    app.run(debug=True)