import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc

df_alunos = pd.read_csv(r'prototiposVisualizacoes/docs/alunosPorCurso.csv')
df_alunos = df_alunos.sort_values('MATR ALUNO')

df_historico = pd.read_csv(r'prototiposVisualizacoes/docs/HistoricoEscolarSimplificado.csv')
df_disciplinas_20232 = pd.read_csv(r'prototiposVisualizacoes/docs/curriculo-20232.csv')
df_disciplinas_20052 = pd.read_csv(r'prototiposVisualizacoes/docs/curriculo-20052.csv')
df_disciplinas_20002 = pd.read_csv(r'prototiposVisualizacoes/docs/curriculo-20002.csv')



disciplinas_list = sorted(
    set(df_disciplinas_20232['COD DISCIPLINA'])
    | set(df_disciplinas_20052['COD DISCIPLINA'])
    | set(df_disciplinas_20002['COD DISCIPLINA'])
)

alunos_dict = dict(
    (str(matricula), idx) for idx, matricula in enumerate(df_alunos['MATR ALUNO'])
)

disciplinas_dict = dict(
    (cod_disciplina, idx) for idx, cod_disciplina in enumerate(disciplinas_list)
)


matriz_geral = {}
matriz_tooltips = {}

n_alunos = len(alunos_dict)
n_disciplinas = len(disciplinas_dict)
matriz_geral = [['' for _ in range(n_disciplinas)] for _ in range(n_alunos)]
matriz_tooltips = [[{} for _ in range(n_disciplinas)] for _ in range(n_alunos)]



for matricula, cod_disciplina, status in zip(df_historico['MATR ALUNO'], df_historico['COD ATIV CURRIC'], df_historico['DESCR SITUACAO']):
    idx_aluno = alunos_dict.get(str(matricula))
    idx_disc = disciplinas_dict.get(cod_disciplina)
    if (
        idx_aluno is not None and idx_disc is not None
        and 0 <= idx_aluno < n_alunos
        and 0 <= idx_disc < n_disciplinas
    ):
        matriz_geral[idx_aluno][idx_disc] = status
    # else:
    #     print(f"Índices fora do range: matricula={matricula}, cod_disciplina={cod_disciplina}, idx_aluno={idx_aluno}, idx_disc={idx_disc}")

for matricula, cod_disciplina, status in zip(df_historico['MATR ALUNO'], df_historico['COD ATIV CURRIC'], df_historico['DESCR SITUACAO']):
    idx_aluno = alunos_dict.get(str(matricula))
    idx_disc = disciplinas_dict.get(cod_disciplina)
    if (
        idx_aluno is not None and idx_disc is not None
        and 0 <= idx_aluno < n_alunos
        and 0 <= idx_disc < n_disciplinas
    ):
        matriz_geral[idx_aluno][idx_disc] = status
        if 'status_list' not in matriz_tooltips[idx_aluno][idx_disc]:
            matriz_tooltips[idx_aluno][idx_disc]['status_list'] = []
        matriz_tooltips[idx_aluno][idx_disc]['status_list'].append(status)


print(matriz_tooltips)





