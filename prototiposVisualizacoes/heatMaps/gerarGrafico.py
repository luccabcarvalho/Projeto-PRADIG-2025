import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc

df = pd.read_csv(r'docs/HistoricoEscolarSimplificado.csv')
df_alunos = pd.read_csv(r'docs/alunosPorCurso.csv')

df_alunos.columns = df_alunos.columns.str.strip()

matricula_id_col = 'MATR ALUNO'  

df = df.sort_values([matricula_id_col, 'COD ATIV CURRIC', 'ANO', 'PERIODO'], ascending=[True, True, True, True])

disciplinas = sorted(df['COD ATIV CURRIC'].unique())
disciplinas_dict = dict(zip(df['COD ATIV CURRIC'], df['NOME ATIV CURRIC']))

mapa_disciplinas = {cod: j for j, cod in enumerate(disciplinas)}
matriculas = df[matricula_id_col].unique()
mapa_matriculas = {mid: i for i, mid in enumerate(matriculas)}

n_matriculas = len(matriculas)
n_disciplinas = len(disciplinas)
matriz = [[[] for _ in range(n_disciplinas)] for _ in range(n_matriculas)]

for (matricula, cod_disc), grupo in df.groupby([matricula_id_col, 'COD ATIV CURRIC']):
    i = mapa_matriculas[matricula]
    j = mapa_disciplinas[cod_disc]
    matriz[i][j] = grupo['DESCR SITUACAO'].astype(str).tolist()

df_matriz = pd.DataFrame(
    [[', '.join(attempts) if attempts else '' for attempts in linha] for linha in matriz],
    index=matriculas,
    columns=[disciplinas_dict[cod] for cod in disciplinas]
)

if 'NOME PESSOA' in df.columns:
    nomes_por_matricula = df.drop_duplicates(matricula_id_col).set_index(matricula_id_col)['NOME PESSOA']
    df_matriz.index = [f"{mid} - {nomes_por_matricula.get(mid, '')}" for mid in df_matriz.index]

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

def classificar_status(cell):
    if pd.isna(cell) or not cell.strip():
        return np.nan
    status_list = [s.strip() for s in cell.split(',') if s.strip()]
    if any(s in aprovados for s in status_list):
        return 1
    if any(s in matriculado for s in status_list):
        return 0
    if any(s in reprovados for s in status_list):
        return -1
    else:
        return 0  

def construir_tooltip(nome_aluno, disciplina, status_str):
    if pd.isna(status_str) or not status_str.strip():
        return (
            f"<b>Aluno:</b> {nome_aluno}<br>"
            f"<b>Disciplina:</b> {disciplina}<br>"
            f"<b>Status:</b> Nenhum"
        )
    status_list = [s.strip() for s in status_str.split(',') if s.strip()]
    status_formatado = ""
    for s in status_list:
        partes = s.split('em')
        status_base = partes[0].strip()
        data = partes[1].strip() if len(partes) > 1 else None

        if status_base in aprovados:
            if data:
                status_formatado += f"Aprovado em <b>{data}</b><br>"
            else:
                status_formatado += "Aprovado<br>"
        elif status_base in reprovados:
            motivo = status_base.split('-')[1].strip() if '-' in status_base else status_base
            if data:
                status_formatado += f"Reprovado por <b>{motivo}</b> em <b>{data}</b><br>"
            else:
                status_formatado += f"Reprovado por <b>{motivo}</b><br>"
        elif status_base in matriculado:
            if data:
                status_formatado += f"Matriculado em <b>{data}</b><br>"
            else:
                status_formatado += "Matriculado<br>"
        else:
            if data:
                status_formatado += f"{status_base} em <b>{data}</b><br>"
            else:
                status_formatado += f"{status_base}<br>"
    status_final = status_list[-1] if status_list else 'Indefinido'
    return (
        f"<b>Aluno:</b> {nome_aluno}<br>"
        f"<b>Disciplina:</b> {disciplina}<br>"
        f"<b>Histórico:</b><br>{status_formatado}"
        f"<b>Status Final:</b> <i>{status_final}</i>"
    )

df_numerico = df_matriz.map(classificar_status)

hover_text = df_matriz.apply(
    lambda row: [
        construir_tooltip(row.name, df_matriz.columns[j], row.iloc[j])
        for j in range(len(row))
    ],
    axis=1
).tolist()

fig = go.Figure(data=go.Heatmap(
    z=df_numerico.values,
    x=df_numerico.columns,
    y=df_numerico.index,
    text=hover_text,
    hoverinfo='text',
    colorscale=[
        [0.0, 'red'],      # -1 → Reprovado/Trancado
        [0.5, 'yellow'],   #  0 → Apenas matriculado
        [1.0, 'green']     #  1 → Aprovado
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