import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc
import time

start_total = time.time()

# Bloco 1: Leitura dos dados
start = time.time()
df_alunos = pd.read_csv(r'prototiposVisualizacoes/docs/alunosPorCurso.csv')
df_historico = pd.read_csv(r'prototiposVisualizacoes/docs/HistoricoEscolarSimplificado.csv')
print(f"Tempo leitura CSVs: {time.time() - start:.3f}s")

# Bloco 2: Preparação de alunos_dict
start = time.time()
df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
alunos = df_historico['MATR ALUNO'].unique().tolist()

alunos_dict = {}
for idx, row in enumerate(df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().itertuples(index=False)):
    alunos_dict[idx] = {
        'MATR ALUNO': row[0],
        'NOME PESSOA': row[1]
    }
print(f"Tempo alunos_dict: {time.time() - start:.3f}s")


# Bloco 3: Preparação de periodos_dict
start = time.time()
periodos_unicos = df_historico[['ANO', 'PERIODO']].drop_duplicates().reset_index(drop=True)
periodos_unicos = periodos_unicos[periodos_unicos['ANO'].astype(str).str.isnumeric()].reset_index(drop=True)

periodos_dict = {}
anos = periodos_unicos['ANO'].values
periodos = periodos_unicos['PERIODO'].values
for idx in range(len(periodos_unicos)):
    periodos_dict[idx] = {
        'ANO': anos[idx],
        'PERIODO': periodos[idx]
    }
print(f"Tempo periodos_dict: {time.time() - start:.3f}s")

def formatar_periodo(ano, periodo):
    periodo = periodo.replace('. semestre', '')
    return f"{str(ano)[-2:]}/{periodo}°"

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
status_matriculado = {'ASC - Matrícula'}

# Bloco 4: Construção da matriz_geral

matriculas_validas = set(alunos_dict[idx]['MATR ALUNO'] for idx in alunos_dict)
periodos_validos = set((periodos_dict[idx]['ANO'], periodos_dict[idx]['PERIODO']) for idx in periodos_dict)

matriz_geral = {}

total_iteracoes_estrutura = 0
total_adicoes_matr = 0
total_adicoes_periodo = 0

start = time.time()
for mt, an, pr in zip(df_historico['MATR ALUNO'], df_historico['ANO'], df_historico['PERIODO']):
    total_iteracoes_estrutura += 1
    matr = mt
    periodo = (an, pr)
    if matr not in matriculas_validas or periodo not in periodos_validos:
        continue
    if matr not in matriz_geral:
        matriz_geral[matr] = {}
        total_adicoes_matr += 1
    if periodo not in matriz_geral[matr]:
        matriz_geral[matr][periodo] = {}
        total_adicoes_periodo += 1
print(f"Tempo matriz_geral (estrutura): {time.time() - start:.3f}s")
print(f"Iterações totais (estrutura): {total_iteracoes_estrutura}")
print(f"Novas matrículas adicionadas: {total_adicoes_matr}")
print(f"Novos períodos adicionados: {total_adicoes_periodo}")

# Bloco 5: Preenchimento da matriz_geral
start = time.time()
total_iteracoes_preenchimento = 0
total_celulas_criadas = 0

matr_aluno = df_historico['MATR ALUNO'].values
anos = df_historico['ANO'].values
periodos = df_historico['PERIODO'].values
nomes_pessoa = df_historico['NOME PESSOA'].values
descr_situacao = df_historico['DESCR SITUACAO'].values
nome_ativ_curric = df_historico['NOME ATIV CURRIC'].values
cod_ativ_curric = df_historico['COD ATIV CURRIC'].values

for i in range(len(df_historico)):
    total_iteracoes_preenchimento += 1
    matr = matr_aluno[i]
    periodo = (anos[i], periodos[i])
    if matr not in matriculas_validas or periodo not in periodos_validos:
        continue
    nome = nomes_pessoa[i]
    status = descr_situacao[i]

    celula = matriz_geral[matr][periodo]
    if not celula:
        matriz_geral[matr][periodo] = {
            'nome': nome,
            'aprovacoes': [],
            'reprovacoes': [],
            'outros': []
        }
        celula = matriz_geral[matr][periodo]
        total_celulas_criadas += 1
    if status in status_aprovados:
        celula['aprovacoes'].append({
            'nome': nome_ativ_curric[i],
            'status': descr_situacao[i],
            'codigo': cod_ativ_curric[i]
        })
    elif status in status_reprovados:
        celula['reprovacoes'].append({
            'nome': nome_ativ_curric[i],
            'status': descr_situacao[i],
            'codigo': cod_ativ_curric[i]
        })
    else:
        celula['outros'].append({
            'nome': nome_ativ_curric[i],
            'status': descr_situacao[i],
            'codigo': cod_ativ_curric[i]
        })
print(f"Tempo matriz_geral (preenchimento): {time.time() - start:.3f}s")
print(f"Iterações totais (preenchimento): {total_iteracoes_preenchimento}")
print(f"Novas células criadas: {total_celulas_criadas}")

# Bloco 6: Construção da matriz_integralizacao
start = time.time()
n_periodos = sum([bloco[1] for bloco in blocos])
matriculas = list(matriz_geral.keys())
matriz_integralizacao = []

for matr in matriculas:
    periodos_ordenados = sorted(
        matriz_geral[matr].keys(),
        key=lambda x: (int(x[0]), 1 if '1' in x[1] else 2)
    )
    linha = []
    for periodo in periodos_ordenados:
        if len(linha) < n_periodos:
            linha.append(formatar_periodo(*periodo))
        else:
            break
    if len(periodos_ordenados) > n_periodos:
        linha[-1] = '+'
    while len(linha) < n_periodos:
        linha.append('')
    matriz_integralizacao.append(linha)
print(f"Tempo matriz_integralizacao: {time.time() - start:.3f}s")

# Bloco 7: Construção do gráfico
start = time.time()
colunas = []
cores = []
for nome, tam, cor in blocos:
    colunas += [nome] + [""] * (tam - 1)
    cores += [cor] * tam

nomes = [
    next((alunos_dict[idx]['NOME PESSOA'] for idx in alunos_dict if alunos_dict[idx]['MATR ALUNO'] == matr), '')
    for matr in matriculas
]

fig = go.Figure(data=go.Heatmap(
    z=[[i for i in range(n_periodos)] for _ in range(len(matriculas))],
    x=[f'{colunas[i]} {i+1}' for i in range(n_periodos)],
    y=[f"{matriculas[i]} - {nomes[i]}" for i in range(len(matriculas))],
    text=matriz_integralizacao,
    hoverinfo='text',
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

print(f"Tempo gráfico: {time.time() - start:.3f}s")

print(f"Tempo total: {time.time() - start_total:.3f}s")

# Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H2("Status de Integralização dos Alunos por Período"),
    dcc.Graph(figure=fig, style={'width': '300vw', 'height': '90vh', 'overflowY': 'scroll'})
])

if __name__ == '__main__':
    app.run(debug=True)