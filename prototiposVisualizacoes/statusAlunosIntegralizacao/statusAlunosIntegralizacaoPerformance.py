import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc


df_alunos = pd.read_csv(r'prototiposVisualizacoes/docs/alunosPorCursoPerformance.csv')
df_historico = pd.read_csv(r'prototiposVisualizacoes/docs/HistoricoEscolarSimplificadoPerformance.csv')

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

matriz_integralizacao = {}

for matr in matriculas_validas:
    matriz_integralizacao[matr] = {}
    for idx, (nome_bloco, qtd_periodos, cor) in enumerate(blocos):
        matriz_integralizacao[matr][idx] = {
            'nome_bloco': nome_bloco,
            'qtd_periodos': qtd_periodos,
            'cor': cor,
            'dados': [] 
        }

for matr in matriz_geral:
    periodos_ordenados = sorted(matriz_geral[matr].keys(), key=lambda x: (int(x[0]), 1 if '1' in x[1] else 2))
    bloco_idx = 0
    periodo_bloco = 0
    excedente = False
    excedente_info = []
    for periodo in periodos_ordenados:
        celula = matriz_geral[matr][periodo]
        if excedente:
            excedente_info.append((formatar_periodo(*periodo), celula))
            continue
        if bloco_idx >= len(blocos):
            break
        nome_bloco, qtd_periodos, cor = blocos[bloco_idx]
        if nome_bloco == 'Situação Irregular' and periodo_bloco >= qtd_periodos:
            # Sinaliza excedente
            excedente = True
            excedente_info.append((formatar_periodo(*periodo), celula))
            continue
        # Adiciona normalmente ao bloco
        matriz_integralizacao[matr][bloco_idx]['dados'].append({
            formatar_periodo(*periodo): celula
        })
        periodo_bloco += 1
        if periodo_bloco >= blocos[bloco_idx][1]:
            bloco_idx += 1
            periodo_bloco = 0
    # Se houve excedente, adiciona tudo ao último bloco com '+'
    if excedente_info:
        matriz_integralizacao[matr][bloco_idx]['dados'].append({
            '+': excedente_info
        })

print(matriz_integralizacao)








