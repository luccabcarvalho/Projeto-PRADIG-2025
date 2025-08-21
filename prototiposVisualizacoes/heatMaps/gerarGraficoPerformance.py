import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc
import time

start_time = time.time()

df_alunos = pd.read_csv(r'prototiposVisualizacoes/docs/alunosPorCurso.csv')

# TODO:
# utilizar sorted para organizar periodos antes de montar o plotly
# no tooltip utilizar a ordenação do mais novo para o mais antigo
# tentar utilizar .sort para cada elemento da matriz de tooltips

df_alunos['MATR ALUNO'] = df_alunos['MATR ALUNO'].astype(str)
df_alunos = df_alunos.drop_duplicates(subset=['MATR ALUNO'])
df_alunos = df_alunos.sort_values('MATR ALUNO').reset_index(drop=True)

df_historico = pd.read_csv(r'prototiposVisualizacoes/docs/HistoricoEscolarSimplificado.csv')
df_disciplinas_20232 = pd.read_csv(r'prototiposVisualizacoes/docs/curriculo-20232.csv')
df_disciplinas_20052 = pd.read_csv(r'prototiposVisualizacoes/docs/curriculo-20052.csv')
df_disciplinas_20002 = pd.read_csv(r'prototiposVisualizacoes/docs/curriculo-20002.csv')
df_disciplinas_20081 = pd.read_csv(r'prototiposVisualizacoes/docs/curriculo-20081.csv')

df_disciplinas_20232 = df_disciplinas_20232[df_disciplinas_20232['TIPO DISCIPLINA'] == 'Obrigatória']
df_disciplinas_20052 = df_disciplinas_20052[df_disciplinas_20052['TIPO DISCIPLINA'] == 'Obrigatória']
df_disciplinas_20002 = df_disciplinas_20002[df_disciplinas_20002['TIPO DISCIPLINA'] == 'Disciplinas obrigatórias']
df_disciplinas_20081 = df_disciplinas_20081[df_disciplinas_20081['TIPO DISCIPLINA'] == 'Obrigatória']

disciplinas_list = sorted(
    set(df_disciplinas_20052['COD DISCIPLINA']) |
    set(df_disciplinas_20002['COD DISCIPLINA']) |
    set(df_disciplinas_20232['COD DISCIPLINA']) |
    set(df_disciplinas_20081['COD DISCIPLINA']) 
)

df_historico['MATR ALUNO'] = df_historico['MATR ALUNO'].astype(str)

alunos_dict = dict(
    (matricula, idx) for idx, matricula in enumerate(df_alunos['MATR ALUNO'])
)
disciplinas_dict = dict(
    (cod_disciplina, idx) for idx, cod_disciplina in enumerate(disciplinas_list)
)

n_alunos = len(alunos_dict)
n_disciplinas = len(disciplinas_dict)
matriz_geral = [['' for _ in range(n_disciplinas)] for _ in range(n_alunos)]
matriz_tooltips = [[{} for _ in range(n_disciplinas)] for _ in range(n_alunos)]

print(f"Total de alunos: {n_alunos}, Total de disciplinas: {n_disciplinas}")


for matricula, cod_disciplina, status in zip(df_historico['MATR ALUNO'], df_historico['COD ATIV CURRIC'], df_historico['DESCR SITUACAO']):
    idx_aluno = alunos_dict.get(str(matricula))
    idx_disc = disciplinas_dict.get(cod_disciplina)
    if (
        idx_aluno is not None and idx_disc is not None
    ):
        matriz_geral[idx_aluno][idx_disc] = status

for matricula, cod_disciplina, status, media_final, ano, periodo, nome, nome_disciplina in zip(
    df_historico['MATR ALUNO'],
    df_historico['COD ATIV CURRIC'],
    df_historico['DESCR SITUACAO'],
    df_historico['MEDIA FINAL'],
    df_historico['ANO'],
    df_historico['PERIODO'],
    df_historico['NOME PESSOA'],
    df_historico['NOME ATIV CURRIC']
):
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
        matriz_tooltips[idx_aluno][idx_disc]['status_list'].append({
            'status': status,
            'media_final': media_final,
            'ano_periodo': f"{ano}-{periodo}"
        })
        if 'aluno' not in matriz_tooltips[idx_aluno][idx_disc]:
            matriz_tooltips[idx_aluno][idx_disc]['aluno'] = []
        matriz_tooltips[idx_aluno][idx_disc]['aluno'].append({
            'nome': nome
        })
        if 'disciplina' not in matriz_tooltips[idx_aluno][idx_disc]:
            matriz_tooltips[idx_aluno][idx_disc]['disciplina'] = []
        matriz_tooltips[idx_aluno][idx_disc]['disciplina'].append({
            'nome_disciplina': nome_disciplina
        })

alunos_labels = [
    f"{matricula} - {df_alunos.loc[df_alunos['MATR ALUNO'] == matricula, 'NOME PESSOA'].values[0]}"
    if not df_alunos.loc[df_alunos['MATR ALUNO'] == matricula, 'NOME PESSOA'].empty else str(matricula)
    for matricula in df_alunos['MATR ALUNO']
]
def get_nome_disciplina(cod):
    for df in [df_disciplinas_20232, df_disciplinas_20052, df_disciplinas_20002, df_disciplinas_20081]:
        nome = df.loc[df['COD DISCIPLINA'] == cod, 'NOME DISCIPLINA']
        if not nome.empty:
            return nome.values[0]
    return str(cod)

disciplinas_labels = [get_nome_disciplina(cod) for cod in disciplinas_list]

aprovados = {
    'APV - Aprovado', 'APV- Aprovado', 'APV - Aprovado sem nota',
    'ADI - Aproveitamento', 'ADI - Dispensa com nota',
    'DIS - Dispensa sem nota', 'ADI - Aproveitamento de créditos da disciplina',
}
reprovados = {
    'REP - Reprovado por nota/conceito',
    'REF - Reprovado por falta',
    'ASC - Reprovado sem nota',
    'TRA - Trancamento de disciplina'
}
matriculado = {'ASC - Matrícula'}

def status_to_num(status):
    if status in aprovados:
        return 1
    if status in matriculado:
        return 0
    if status in reprovados:
        return -1
    return np.nan

matriz_numerica = [
    [status_to_num(cell) for cell in row]
    for row in matriz_geral
]

def tooltip_format(cell_tooltip):
    if not cell_tooltip or 'status_list' not in cell_tooltip:
        return ""
    lines = []
    for s in sorted(cell_tooltip['status_list'], key=lambda x: x.get('ano_periodo', ''), reverse=True):
        status = s.get('status', '')
        media = s.get('media_final', '')
        periodo = s.get('ano_periodo', '')
        lines.append(f"{status} (Nota: {media}, Período: {periodo})")
    return "<br>".join(lines)

matriz_tooltips_str = [
    [tooltip_format(cell) for cell in row]
    for row in matriz_tooltips
]

fig = go.Figure(data=go.Heatmap(
    z=matriz_numerica,
    x=disciplinas_labels,
    y=alunos_labels,
    text=matriz_tooltips_str,
    hoverinfo='text',
    colorscale=[
        [0.0, 'red'],
        [0.5, 'yellow'],
        [1.0, 'green']
    ],
    colorbar=dict(
        title='Status',
        tickvals=[-1, 0, 1],
        ticktext=['Reprovado/Trancado', 'Matriculado', 'Aprovado']
    )
))

fig.update_layout(
    title='Desempenho Acadêmico por Matrícula e Disciplina',
    xaxis=dict(title='Disciplinas', tickangle=45, tickfont=dict(size=9)),
    yaxis=dict(title='Matrículas', tickfont=dict(size=9)),
    autosize=True,
    margin=dict(l=50, r=50, t=80, b=100),
    height=1200,
)

app = Dash(__name__)
app.layout = html.Div([
    html.H2("Heatmap de Desempenho Acadêmico"),
    dcc.Graph(figure=fig, style={'width': '100vw', 'height': '100vh'})
])

if __name__ == '__main__':
    app.run(debug=True)

end_time = time.time()
print(end_time - start_time)





