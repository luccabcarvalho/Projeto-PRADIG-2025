import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc

# Leitura dos dados
df_alunos = pd.read_csv(r'docs/alunosPorCurso.csv')
df_hist = pd.read_csv(r'docs/HistoricoEscolarSimplificado.csv')

df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
alunos = df_alunos['NOME PESSOA'].tolist()

blocos = [
    ('Prazo Previsto', 8, '#6fa8dc'),
    ('Prazo Máximo', 2, '#9fc5e8'),
    ('Exigir plano de integralização', 2, '#f6b26b'),
    ('Prorrogação Máxima', 2, '#f9cb9c'),
    ('Situação Irregular', 2, '#e06666'),
    # ('Mobilidade', 1, '#93c47d'),
    # ('Períodos Excepcionais', 3, '#ffe599'),
    # ('Atividades Calendário Emergencial', 2, '#ffd966'),
    # ('Trancamentos Totais (regulares)', 2, '#b7b7b7'),
    # ('Trancamentos Totais (especiais)', 2, '#cccccc'),
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
aluno_periodos = {aluno: [] for aluno in alunos}
mapa_nome_id = dict(zip(df_alunos['NOME PESSOA'], df_alunos['ID PESSOA']))

for _, row in df_hist.iterrows():
    nome = df_alunos.loc[df_alunos['ID PESSOA'] == row['ID PESSOA'], 'NOME PESSOA']
    if not nome.empty:
        aluno = nome.values[0]
        periodo = row['PERIODO_LABEL']
        if periodo not in aluno_periodos[aluno]:
            aluno_periodos[aluno].append(periodo)

def tooltip_periodo(aluno_nome, periodo):
    # Seleciona o id do aluno
    id_pessoa = mapa_nome_id.get(aluno_nome)
    if not id_pessoa:
        return periodo

    # Filtra o histórico do aluno para o período
    dados = df_hist[(df_hist['ID PESSOA'] == id_pessoa) & (df_hist['PERIODO_LABEL'] == periodo)]
    if dados.empty:
        return periodo

    # Agrupa disciplinas por status
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
for aluno in alunos:
    periodos = aluno_periodos[aluno]
    linha = []
    tooltips = []
    if len(periodos) <= n_periodos:
        for i in range(n_periodos):
            if i < len(periodos):
                linha.append(periodos[i])
                tooltips.append(tooltip_periodo(aluno, periodos[i]))
            else:
                linha.append('')
                tooltips.append('')
    else:
        for i in range(n_periodos - 1):
            linha.append(periodos[i])
            tooltips.append(tooltip_periodo(aluno, periodos[i]))
        linha.append('+')
        excedentes = periodos[n_periodos - 1:]
        tooltips.append('Períodos excedentes: ' + ', '.join(excedentes))
    matriz.append(linha)
    tooltip_matriz.append(tooltips)

# Geração do heatmap
fig = go.Figure(data=go.Heatmap(
    z=[[i for i in range(n_periodos)] for _ in range(len(alunos))],
    x=[f'{colunas[i]} {i+1}' for i in range(n_periodos)],
    y=alunos,
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

# Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H2("Status de Integralização dos Alunos por Período"),
    dcc.Graph(figure=fig, style={'width': '300vw', 'height': '90vh', 'overflowY': 'scroll'})
])

if __name__ == '__main__':
    app.run(debug=True)


