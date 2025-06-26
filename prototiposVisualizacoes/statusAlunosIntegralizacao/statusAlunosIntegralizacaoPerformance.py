import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc


df_alunos = pd.read_csv(r'prototiposVisualizacoes/docs/alunosPorCurso.csv')
df_historico = pd.read_csv(r'prototiposVisualizacoes/docs/HistoricoEscolarSimplificado.csv')

df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
alunos = df_historico['MATR ALUNO'].unique().tolist()

alunos_dict = {}
for idx, row in enumerate(df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().itertuples(index=False)):
    alunos_dict[idx] = {
        'MATR ALUNO': row[0],
        'NOME PESSOA': row[1]
    }

periodos_unicos = df_historico[['ANO', 'PERIODO']].drop_duplicates().reset_index(drop=True)
periodos_unicos = periodos_unicos[periodos_unicos['ANO'].astype(str).str.isnumeric()].reset_index(drop=True)

periodos_dict = {}
for idx, row in periodos_unicos.iterrows():
    periodos_dict[idx] = {
        'ANO': row['ANO'],
        'PERIODO': row['PERIODO']
    }

def formatar_periodo(ano, periodo):
    return f"{ano}/{periodo}"

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

status_aprovados = {
    'APV - Aprovado', 'APV- Aprovado', 'APV - Aprovado sem nota',
    'ADI - Aproveitamento', 'ADI - Aproveitamento de créditos da disciplina',
    'ADI - Dispensa com nota', 'DIS - Dispensa sem nota'
}
status_reprovados = {
    'REP - Reprovado por nota/conceito', 'REF - Reprovado por falta',
    'ASC - Reprovado sem nota', 'TRA - Trancamento de disciplina'
}
status_outros = {
    
}
status_matriculado = {'ASC - Matrícula'}

matriculas_validas = set(alunos_dict[idx]['MATR ALUNO'] for idx in alunos_dict)
periodos_validos = set((periodos_dict[idx]['ANO'], periodos_dict[idx]['PERIODO']) for idx in periodos_dict)

matriz_geral = {}

for _, row in df_historico.iterrows():
    matr = row['MATR ALUNO']
    periodo = (row['ANO'], row['PERIODO'])
    if matr not in matriculas_validas or periodo not in periodos_validos:
        continue
    if matr not in matriz_geral:
        matriz_geral[matr] = {}
    if periodo not in matriz_geral[matr]:
        matriz_geral[matr][periodo] = {}


for _, row in df_historico.iterrows():
    matr = row['MATR ALUNO']
    periodo = (row['ANO'], row['PERIODO'])
    if matr not in matriculas_validas or periodo not in periodos_validos:
        continue
    nome = row['NOME PESSOA']
    status = row['DESCR SITUACAO']

    celula = matriz_geral[matr][periodo]
    if not celula:
        matriz_geral[matr][periodo] = {
            'nome': nome,
            'aprovacoes': [],
            'reprovacoes': [],
            'outros': []
        }
        celula = matriz_geral[matr][periodo]
    if status in status_aprovados:
        celula['aprovacoes'].append({
            'nome': row['NOME ATIV CURRIC'],
            'status': row['DESCR SITUACAO'],
            'codigo': row['COD ATIV CURRIC']
        })
    elif status in status_reprovados:
        celula['reprovacoes'].append({
            'nome': row['NOME ATIV CURRIC'],
            'status': row['DESCR SITUACAO'],
            'codigo': row['COD ATIV CURRIC']
        })
    else:
        celula['outros'].append({
            'nome': row['NOME ATIV CURRIC'],
            'status': row['DESCR SITUACAO'],
            'codigo': row['COD ATIV CURRIC']
        })

colunas = []
cores = []
for nome, tam, cor in blocos:
    colunas += [nome] + [""] * (tam - 1)
    cores += [cor] * tam
n_periodos = len(colunas)

# Geração dos labels dos períodos para cada (ano, periodo)
periodo_label_dict = {}
for idx, row in periodos_unicos.iterrows():
    ano = str(row['ANO'])
    periodo = str(row['PERIODO']).replace('. semestre', '').strip()
    label = ano[-2:] + '/' + periodo
    periodo_label_dict[(row['ANO'], row['PERIODO'])] = label

# Mapeamento matrícula -> nome
mapa_matricula_nome = {alunos_dict[idx]['MATR ALUNO']: alunos_dict[idx]['NOME PESSOA'] for idx in alunos_dict}

# Para cada aluno, lista de períodos ordenados
aluno_periodos = {}
for matr in matriz_geral:
    periodos = list(matriz_geral[matr].keys())
    # Ordena por ano e período
    periodos.sort()
    labels = [periodo_label_dict.get(p, '') for p in periodos]
    aluno_periodos[matr] = labels

# Função para gerar tooltip a partir da célula já montada
def gerar_tooltip_celula(matr, periodo):
    celula = matriz_geral[matr][periodo]
    nome = celula.get('nome', str(matr))
    periodo_label = periodo_label_dict.get(periodo, f"{periodo[0]}/{periodo[1]}")
    aprovadas = [f"{d['codigo']} - {d['nome']}" for d in celula.get('aprovacoes', [])]
    reprovadas = [f"{d['codigo']} - {d['nome']}" for d in celula.get('reprovacoes', [])]
    outros = [f"{d['codigo']} - {d['nome']} [{d['status']}]" for d in celula.get('outros', [])]
    tooltip = f"<b>Aluno:</b> {nome}<br><b>Período:</b> {periodo_label}<br>"
    if aprovadas:
        tooltip += "<b>Aprovadas:</b><br>" + "<br>".join(aprovadas) + "<br>"
    if reprovadas:
        tooltip += "<b>Reprovadas:</b><br>" + "<br>".join(reprovadas) + "<br>"
    if outros:
        tooltip += "<b>Outros:</b><br>" + "<br>".join(outros) + "<br>"
    return tooltip

# Lista de matrículas na mesma ordem dos alunos
matriculas = list(matriz_geral.keys())

# Montagem das matrizes para plotly
matriz = np.full((len(matriculas), n_periodos), '', dtype=object)
tooltip_matriz = np.full((len(matriculas), n_periodos), '', dtype=object)

aluno_labels_tooltips = {}
for matr in matriculas:
    periodos = sorted(matriz_geral[matr].keys())
    labels = [periodo_label_dict.get(p, '') for p in periodos]
    tooltips = [gerar_tooltip_celula(matr, p) for p in periodos]
    aluno_labels_tooltips[matr] = (labels, tooltips)

for idx, matr in enumerate(matriculas):
    labels, tooltips = aluno_labels_tooltips[matr]
    limite = min(len(labels), n_periodos)
    if limite > 0:
        matriz[idx, :limite] = labels[:limite]
        tooltip_matriz[idx, :limite] = tooltips[:limite]
    if len(labels) > n_periodos:
        matriz[idx, -1] = '+'
        excedentes = labels[n_periodos - 1:]
        tooltip_matriz[idx, -1] = 'Períodos excedentes: ' + ', '.join(excedentes)

fig = go.Figure(data=go.Heatmap(
    z=[[i for i in range(n_periodos)] for _ in range(len(matriculas))],
    x=[f'{colunas[i]} {i+1}' for i in range(n_periodos)],
    y=[f"{matr} - {mapa_matricula_nome.get(matr, '')}" for matr in matriculas],
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
        y0=-0.5, y1=len(matriculas)-0.5,
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
        range=[-0.5, n_periodos-0.5]
    ),
    yaxis=dict(
        automargin=True,
        tickfont=dict(size=12),
        scaleanchor="x",
        scaleratio=1,
        range=[-0.5, len(matriculas)-0.5]
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















