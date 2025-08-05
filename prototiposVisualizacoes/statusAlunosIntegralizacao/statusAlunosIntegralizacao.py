import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc

# Leitura dos dados
df_alunos = pd.read_csv(r'prototiposVisualizacoes/docs/alunosPorCurso.csv')
df_hist = pd.read_csv(r'prototiposVisualizacoes/docs/HistoricoEscolarSimplificado.csv')

df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
alunos = df_hist['MATR ALUNO'].unique().tolist()

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
df_hist = df_hist[df_hist['PERIODO_LABEL'].notna()]

mapa_matricula_nome = dict(zip(df_hist['MATR ALUNO'], df_hist['NOME PESSOA']))

aluno_periodos_df = df_hist[['MATR ALUNO', 'PERIODO_LABEL']].drop_duplicates()
aluno_periodos_grouped = aluno_periodos_df.groupby('MATR ALUNO')['PERIODO_LABEL'].apply(list)
aluno_periodos = aluno_periodos_grouped.to_dict()

df_hist_tooltip = df_hist.copy()
df_hist_tooltip['DISCIPLINA_FORMATADA'] = (
    df_hist_tooltip['COD ATIV CURRIC'].astype(str) + ' - ' +
    df_hist_tooltip['NOME ATIV CURRIC'] + ' (' +
    df_hist_tooltip['TOTAL CARGA HORARIA'].astype(str) + 'h)'
)
df_hist_tooltip.set_index(['MATR ALUNO', 'PERIODO_LABEL'], inplace=True)

def gerar_tooltip(grupo):
    aluno_nome = mapa_matricula_nome.get(grupo.name[0], str(grupo.name[0]))
    periodo = grupo.name[1]
    aprovadas = grupo.loc[grupo['DESCR SITUACAO'].isin(status_aprovados), 'DISCIPLINA_FORMATADA'].tolist()
    reprovadas = grupo.loc[grupo['DESCR SITUACAO'].isin(status_reprovados), 'DISCIPLINA_FORMATADA'].tolist()
    matriculadas = grupo.loc[grupo['DESCR SITUACAO'].isin(status_matriculado), 'DISCIPLINA_FORMATADA'].tolist()
    outros = [
        f"{row['DISCIPLINA_FORMATADA']} [{row['DESCR SITUACAO']}]"
        for _, row in grupo.iterrows()
        if row['DESCR SITUACAO'] not in status_aprovados
        and row['DESCR SITUACAO'] not in status_reprovados
        and row['DESCR SITUACAO'] not in status_matriculado
    ]
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

tooltips_df = df_hist_tooltip.groupby(['MATR ALUNO', 'PERIODO_LABEL']).apply(gerar_tooltip)

matriz = np.full((len(alunos), n_periodos), '', dtype=object)
tooltip_matriz = np.full((len(alunos), n_periodos), '', dtype=object)

for idx, matricula in enumerate(alunos):
    periodos = aluno_periodos.get(matricula, [])
    limite = min(len(periodos), n_periodos)
    if limite > 0:
        matriz[idx, :limite] = periodos[:limite]
        tooltip_matriz[idx, :limite] = [
            tooltips_df.get((matricula, periodo), periodo)
            for periodo in periodos[:limite]
        ]
    if len(periodos) > n_periodos:
        matriz[idx, -1] = '+'
        excedentes = periodos[n_periodos - 1:]
        tooltip_matriz[idx, -1] = 'Períodos excedentes: ' + ', '.join(excedentes)

# Geração do heatmap
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

# Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H2("Status de Integralização dos Alunos por Período"),
    dcc.Graph(figure=fig, style={'width': '300vw', 'height': '90vh', 'overflowY': 'scroll'})
])

if __name__ == '__main__':
    app.run(debug=True)